cmake_minimum_required(VERSION 3.10)
project(FPSI)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

list(PREPEND CMAKE_PREFIX_PATH "${CMAKE_SOURCE_DIR}/thirdparty/out/install")

find_package(cryptoTools REQUIRED)
find_package(libOTe REQUIRED)
find_package(volePSI REQUIRED)
find_package(fmt REQUIRED)

set(FPSI_SOURCES
    # Application entry point
    fpsi/main.cpp

    # Shared configuration and utilities
    fpsi/tool/common.cpp
    fpsi/tool/config.cpp
    fpsi/data/genData.cpp
    fpsi/data/fileIO.cpp

    # Reusable protocol primitives
    fpsi/primitive/b2a.cpp
    fpsi/primitive/cmp.cpp
    fpsi/primitive/eq.cpp
    fpsi/primitive/mul.cpp
    fpsi/primitive/mux.cpp
    fpsi/primitive/OKVS.cpp
    fpsi/primitive/SoOPRF.cpp
    fpsi/primitive/SoOPPRF.cpp

    # FPSI protocol compositions
    fpsi/protocol/uniqueBlock.cpp
    fpsi/protocol/uniqueCell.cpp
)

add_executable(fpsi ${FPSI_SOURCES})

target_include_directories(fpsi PRIVATE
    ${CMAKE_SOURCE_DIR}
    ${CMAKE_SOURCE_DIR}/thirdparty/out/install/include
    ${CMAKE_SOURCE_DIR}/thirdparty/out/install/include/secureJoin
)

target_link_libraries(fpsi PRIVATE oc::cryptoTools oc::libOTe visa::volePSI fmt::fmt)
target_link_libraries(fpsi PRIVATE ${CMAKE_SOURCE_DIR}/thirdparty/out/install/lib/libsecureJoin.a)
target_link_libraries(fpsi PRIVATE ${CMAKE_SOURCE_DIR}/thirdparty/out/install/lib/libblake3.a)

if(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64|i.86")
    target_compile_options(fpsi PRIVATE -mpclmul -maes -msse2 -msse4.1)
endif()

include(CTest)
if(BUILD_TESTING)
    add_test(NAME artifact_cli_help COMMAND fpsi -h)
    add_test(
        NAME artifact_file_input
        COMMAND python3 ${CMAKE_SOURCE_DIR}/../scripts/test_file_input.py $<TARGET_FILE:fpsi>
    )
    set_tests_properties(artifact_file_input PROPERTIES TIMEOUT 240)
    add_test(
        NAME artifact_boundary_inputs
        COMMAND python3 ${CMAKE_SOURCE_DIR}/../scripts/test_boundary_inputs.py
            --binary $<TARGET_FILE:fpsi>
            --output-dir ${CMAKE_CURRENT_BINARY_DIR}/boundary-results
    )
    set_tests_properties(artifact_boundary_inputs PROPERTIES TIMEOUT 600)
    add_test(
        NAME artifact_boundary_workflow
        COMMAND python3 ${CMAKE_SOURCE_DIR}/../scripts/test_boundary_workflow.py
    )
    set_tests_properties(artifact_boundary_workflow PROPERTIES TIMEOUT 60)
    add_test(
        NAME artifact_trials_workflow
        COMMAND python3 ${CMAKE_SOURCE_DIR}/../scripts/test_trials.py
    )
    set_tests_properties(artifact_trials_workflow PROPERTIES TIMEOUT 120)
    add_test(
        NAME artifact_paper_comparison
        COMMAND python3 ${CMAKE_SOURCE_DIR}/../scripts/test_paper_comparison.py
    )
    set_tests_properties(artifact_paper_comparison PROPERTIES TIMEOUT 60)
    add_test(
        NAME artifact_smoke
        COMMAND bash ${CMAKE_SOURCE_DIR}/../scripts/run_smoke.sh $<TARGET_FILE:fpsi>
    )
    set_tests_properties(artifact_smoke PROPERTIES TIMEOUT 120)
    add_test(
        NAME artifact_result_parser
        COMMAND python3 ${CMAKE_SOURCE_DIR}/../scripts/summarize_results.py --self-test
    )
endif()
