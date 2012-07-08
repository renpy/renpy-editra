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
        profiler.Profile_Set("DEFAULT_LEX", "Ren'Py")
        profiler.Profile_Set("LEXERMENU", [ "Ren'Py" ])

        # Set the RENPY_VERSION setting to store the version of 
        # the Ren'Py profile in use.
        profiler.Profile_Set("RENPY_VERSION", 3)

try:
    setup_profile()
except:
    import traceback
    traceback.print_exc()

