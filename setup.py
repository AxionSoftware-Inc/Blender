from setuptools import Extension, setup


setup(
    ext_modules=[
        Extension(
            "spectra._native_cpu",
            sources=["native/spectra_native_cpu.c"],
        )
    ]
)
