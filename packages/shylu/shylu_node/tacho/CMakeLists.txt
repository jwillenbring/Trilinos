TRIBITS_SUBPACKAGE(Tacho)

IF (Kokkos_ENABLE_CUDA)
  # Tacho requires CUDA >= 8.0.
  IF (DEFINED CUDA_VERSION AND (CUDA_VERSION VERSION_LESS "8.0"))
    MESSAGE(FATAL_ERROR "Tacho requires CUDA 8 if CUDA is enabled")
  ENDIF()
ENDIF()

IF (Kokkos_ENABLE_HIP)
  IF (NOT (TPL_ENABLE_ROCBLAS AND TPL_ENABLE_ROCSPARSE AND TPL_ENABLE_ROCSOLVER))
    MESSAGE(FATAL_ERROR "Tacho can not be build with HIP without enabling ROCBLAS, ROCSPARSE, and ROCSOLVER TPLs. Please disable Tacho, or enable these three TPLs")
  ENDIF()
ENDIF()

IF (Kokkos_ENABLE_THREADS)
  IF (NOT Kokkos_ENABLE_OPENMP)
    MESSAGE(FATAL_ERROR "Tacho can not be build with Pthreads as the Kokkos Host Backend.")
  ENDIF()
ENDIF()

ADD_SUBDIRECTORY(src)

IF (NOT DEFINED Tacho_ENABLE_EXAMPLES)
  SET(Tacho_ENABLE_EXAMPLES ${Trilinos_ENABLE_EXAMPLES})
ENDIF()
IF (NOT DEFINED Tacho_ENABLE_TESTS)
  SET(Tacho_ENABLE_TESTS ${Trilinos_ENABLE_TESTS})
ENDIF()

IF (Tacho_ENABLE_EXAMPLES)
  TRIBITS_ADD_EXAMPLE_DIRECTORIES(example)
ENDIF()

IF (Tacho_ENABLE_TESTS)
  TRIBITS_ADD_TEST_DIRECTORIES(unit-test)
ENDIF()

TRIBITS_SUBPACKAGE_POSTPROCESS()
