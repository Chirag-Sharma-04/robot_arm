import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument , SetEnvironmentVariable , IncludeLaunchDescription #include is used to include another launch file
from launch.substitutions import Command , LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python import get_package_share_directory
from pathlib import Path




def generate_launch_description():

    ros_distro = os.environ["ROS_DISTRO"]

    is_ignition = "True" if ros_distro == "humble" else "False"

    model_arg= DeclareLaunchArgument(
        name="model" , 
        default_value=os.path.join(get_package_share_directory("robot_description"), "urdf" ,"robot.urdf.xacro"),
        description="Absolute path to the robot URDF"
    )
    
    robot_description= ParameterValue(Command([
        "xacro ", 
        LaunchConfiguration("model"),
        " is_ignition:=",
        is_ignition
        ]),
        value_type=str)  #converting xacro to urdf format
    
    package_dir=get_package_share_directory("robot_description") #gets the path of the package

    gazebo_resource_path=SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=[
            str(Path(package_dir).parent.resolve())
            ]
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description,
                     "use_sim_time":True}]
    )

    
    phy_engine = "" if ros_distro == "humble" else "-physics-engine gz-physics-bullet-featherstone-plugin"

    #launching another launch file 
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("ros_gz_sim"),
                "launch" 
            ), "/gz_sim.launch.py"]
        ),
        launch_arguments=[
            ("gz_args",[" -v 4 -r empty.sdf " , phy_engine])
        ]
    )

    gz_spawn_entity= Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=["-topic","robot_description",
                   "-name", "robot_arm"]
    )

    gz_ros2_bridge= Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/clock@rosgraph_msg/msg/Clock[gz.msgs.Clock"
        ]
    )

    return LaunchDescription([
        model_arg,
        robot_state_publisher,
        gazebo_resource_path,
        gazebo,
        gz_spawn_entity,
        gz_ros2_bridge

    ])