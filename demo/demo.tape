Output demo/retro_demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 900
Set Height 650
Set Theme "Dracula"
Set Padding 20
Set TypingSpeed 40ms
Set PlaybackSpeed 0.75

# Start in project directory
Type "cd ~/projects/sprint-retro-ai"
Enter
Sleep 300ms

# Show the project files
Type "ls"
Enter
Sleep 800ms

# Run the demo
Type "python3 demo/mock_retro.py"
Enter
Sleep 3s

# Scroll pause so viewer can read the output
Sleep 4s
