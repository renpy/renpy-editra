import profiler

############################################################################### 
# Change some of the default settings in the profile.

def setup_profile():

    version = profiler.Profile_Get("RENPY_VERSION", default=0)
    
    if version < 2:
        profiler.Profile_Set("CHECKUPDATE", False)
        profiler.Profile_Set("AALIASING", True)

    if version < 3:    
        profiler.Profile_Set("SYNTHEME", "RenPy")

    if version < 4:
        profiler.Profile_Set("LEXERMENU", [ "Ren'Py" ])
        profiler.Profile_Set("DEFAULT_LEX", "Ren'Py")

    if version < 5:
        profiler.Profile_Set("APPSPLASH", False)

    if version < 6:
        profiler.Profile_Set("SHOW_EDGE", False)

        # Set the RENPY_VERSION setting to store the version of 
        # the Ren'Py profile in use.
        profiler.Profile_Set("RENPY_VERSION", 6)

def init():
    setup_profile()

