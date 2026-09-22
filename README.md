# iSnake

A Snake game reimplementation written in Python with Kivy, featuring a playable game mode and an automated Snake Solver.

The project focuses on a custom interface and configurable gameplay, with the Android APK built using APKVolt.

## Features

- Classic Snake gameplay
- Snake Solver mode
- Apple-based scoring system
- Game timer with millisecond precision
- Configurable movement speed limit
- Pause, resume and replay
- Toggleable visual gradient
- Responsive UI built with Kivy
- Custom fonts and graphical interface
- UI scaling based on screen size
- Android APK build using APKVolt

## Game Modes

#### Play

Play Snake manually while keeping track of your score, elapsed time and movement speed.

#### Snake Solver

An automated mode where the snake is controlled by a solver that determines its movements based on the current game state, using safe-move logic and the Wavefront algorithm.

## Interface

iSnake uses a custom dark interface with rounded elements, custom typography and interactive controls.

### The game interface provides:

- Current apple count
- Game timer
- Current movement speed
- Configurable speed limit
- Pause and replay controls
- Visual gradient toggle

## Technologies

- Python
- Kivy
- Kivy Language (.kv)
- APKVolt

## Building

The project is developed with Kivy and can be packaged as an Android application using APKVolt.

## License

MIT License.