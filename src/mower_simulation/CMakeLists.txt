cmake_minimum_required(VERSION 3.8)
project(mower_simulation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY worlds launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
