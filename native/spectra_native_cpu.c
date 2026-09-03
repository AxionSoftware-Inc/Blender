#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *state_tuple_from_array(const double *state, Py_ssize_t size) {
    PyObject *tuple = PyTuple_New(size);
    if (tuple == NULL) {
        return NULL;
    }
    for (Py_ssize_t i = 0; i < size; ++i) {
        PyObject *value = PyFloat_FromDouble(state[i]);
        if (value == NULL) {
            Py_DECREF(tuple);
            return NULL;
        }
        PyTuple_SET_ITEM(tuple, i, value);
    }
    return tuple;
}

static int sequence_to_array(PyObject *value, double *out, Py_ssize_t size, const char *label) {
    PyObject *sequence = PySequence_Fast(value, label);
    if (sequence == NULL) {
        return -1;
    }
    if (PySequence_Fast_GET_SIZE(sequence) != size) {
        PyErr_SetString(PyExc_ValueError, "ODE derivative dimension mismatch");
        Py_DECREF(sequence);
        return -1;
    }
    PyObject **items = PySequence_Fast_ITEMS(sequence);
    for (Py_ssize_t i = 0; i < size; ++i) {
        double number = PyFloat_AsDouble(items[i]);
        if (PyErr_Occurred()) {
            Py_DECREF(sequence);
            return -1;
        }
        out[i] = number;
    }
    Py_DECREF(sequence);
    return 0;
}

static int call_derivative(
    PyObject *derivative,
    double time,
    const double *state,
    Py_ssize_t size,
    double *out
) {
    PyObject *time_object = PyFloat_FromDouble(time);
    PyObject *state_object = state_tuple_from_array(state, size);
    if (time_object == NULL || state_object == NULL) {
        Py_XDECREF(time_object);
        Py_XDECREF(state_object);
        return -1;
    }

    PyObject *result = PyObject_CallFunctionObjArgs(
        derivative,
        time_object,
        state_object,
        NULL
    );
    Py_DECREF(time_object);
    Py_DECREF(state_object);
    if (result == NULL) {
        return -1;
    }

    int status = sequence_to_array(
        result,
        out,
        size,
        "ODE derivative must return a sequence"
    );
    Py_DECREF(result);
    return status;
}

static PyObject *native_solve_rk4(PyObject *self, PyObject *args) {
    (void)self;
    PyObject *derivative = NULL;
    PyObject *initial_state_object = NULL;
    double initial_time = 0.0;
    double end_time = 0.0;
    Py_ssize_t steps = 0;

    if (!PyArg_ParseTuple(
            args,
            "OdOdn",
            &derivative,
            &initial_time,
            &initial_state_object,
            &end_time,
            &steps)) {
        return NULL;
    }
    if (!PyCallable_Check(derivative)) {
        PyErr_SetString(PyExc_TypeError, "derivative must be callable");
        return NULL;
    }
    if (steps < 1) {
        PyErr_SetString(PyExc_ValueError, "steps must be >= 1");
        return NULL;
    }
    if (!(end_time > initial_time)) {
        PyErr_SetString(PyExc_ValueError, "end_time must be greater than initial_time");
        return NULL;
    }

    PyObject *initial_sequence = PySequence_Fast(
        initial_state_object,
        "initial_state must be a sequence"
    );
    if (initial_sequence == NULL) {
        return NULL;
    }
    Py_ssize_t size = PySequence_Fast_GET_SIZE(initial_sequence);
    if (size < 1) {
        Py_DECREF(initial_sequence);
        PyErr_SetString(PyExc_ValueError, "ODE initial_state cannot be empty");
        return NULL;
    }

    double *buffer = PyMem_Malloc((size_t)(6 * size) * sizeof(double));
    if (buffer == NULL) {
        Py_DECREF(initial_sequence);
        return PyErr_NoMemory();
    }
    double *state = buffer;
    double *k1 = state + size;
    double *k2 = k1 + size;
    double *k3 = k2 + size;
    double *k4 = k3 + size;
    double *temporary = k4 + size;

    PyObject **initial_items = PySequence_Fast_ITEMS(initial_sequence);
    for (Py_ssize_t i = 0; i < size; ++i) {
        state[i] = PyFloat_AsDouble(initial_items[i]);
        if (PyErr_Occurred()) {
            PyMem_Free(buffer);
            Py_DECREF(initial_sequence);
            return NULL;
        }
    }
    Py_DECREF(initial_sequence);

    PyObject *times = PyTuple_New(steps + 1);
    PyObject *states = PyTuple_New(steps + 1);
    if (times == NULL || states == NULL) {
        Py_XDECREF(times);
        Py_XDECREF(states);
        PyMem_Free(buffer);
        return NULL;
    }

    const double dt = (end_time - initial_time) / (double)steps;
    double time = initial_time;

    for (Py_ssize_t step = 0; step <= steps; ++step) {
        PyObject *time_value = PyFloat_FromDouble(time);
        PyObject *state_value = state_tuple_from_array(state, size);
        if (time_value == NULL || state_value == NULL) {
            Py_XDECREF(time_value);
            Py_XDECREF(state_value);
            Py_DECREF(times);
            Py_DECREF(states);
            PyMem_Free(buffer);
            return NULL;
        }
        PyTuple_SET_ITEM(times, step, time_value);
        PyTuple_SET_ITEM(states, step, state_value);

        if (step == steps) {
            break;
        }

        if (call_derivative(derivative, time, state, size, k1) < 0) {
            goto error;
        }
        for (Py_ssize_t i = 0; i < size; ++i) {
            temporary[i] = state[i] + 0.5 * dt * k1[i];
        }
        if (call_derivative(derivative, time + 0.5 * dt, temporary, size, k2) < 0) {
            goto error;
        }
        for (Py_ssize_t i = 0; i < size; ++i) {
            temporary[i] = state[i] + 0.5 * dt * k2[i];
        }
        if (call_derivative(derivative, time + 0.5 * dt, temporary, size, k3) < 0) {
            goto error;
        }
        for (Py_ssize_t i = 0; i < size; ++i) {
            temporary[i] = state[i] + dt * k3[i];
        }
        if (call_derivative(derivative, time + dt, temporary, size, k4) < 0) {
            goto error;
        }

        for (Py_ssize_t i = 0; i < size; ++i) {
            state[i] += dt * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) / 6.0;
        }
        time += dt;
    }

    PyMem_Free(buffer);
    return Py_BuildValue("NN", times, states);

error:
    Py_DECREF(times);
    Py_DECREF(states);
    PyMem_Free(buffer);
    return NULL;
}

static PyMethodDef module_methods[] = {
    {
        "solve_rk4",
        native_solve_rk4,
        METH_VARARGS,
        "Integrate a first-order system with a native fixed-step RK4 loop."
    },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "_native_cpu",
    "Spectra optional native CPU numerical kernels.",
    -1,
    module_methods
};

PyMODINIT_FUNC PyInit__native_cpu(void) {
    return PyModule_Create(&module_definition);
}
