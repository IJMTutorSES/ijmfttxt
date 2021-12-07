import ijmfttxt

# Initialize and setup Connection to TXT Controller
keyboard = ijmfttxt.Keyboard()

while True:
    # While space is pressed print "Hallo" five times
    if keyboard.isPressed("space", 5):
        print("Hallo")

    # while e is pressed print "Auf Wiedersehen" once
    if keyboard.isPressed("e", 1):
        print("Auf Wiedersehen")

    # while a is pressed print "Test"
    if keyboard.isPressed("a"):
        print("Test")
