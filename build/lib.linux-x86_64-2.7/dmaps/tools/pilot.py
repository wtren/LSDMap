import os
import sys
import radical.pilot

def pilot_state_cb(pilot, state):
    """pilot_state_change_cb() is a callback function. It gets called very
    time a ComputePilot changes its state.
    """

    # Mitigate the erroneous management of the pilot state from the RP
    # back-end. In some conditions, the callback is called when the state of
    # the pilot is not available even if it should be.
    if pilot:

        print "[Callback]: ComputePilot '{0}' state changed to {1}.".format(
            pilot.uid, state)

        if state == radical.pilot.states.FAILED:
            print "#######################"
            print "##       ERROR       ##"
            print "#######################"
            print "Pilot {0} has FAILED. Can't recover.".format(pilot.uid)
            print "Pilot log: {0}".format(pilot.log)
            sys.exit(1)

def unit_state_change_cb(unit, state):
    """unit_state_change_cb() is a callback function. It gets called very
    time a ComputeUnit changes its state.
    """

    if unit:
        print "[Callback]: ComputeUnit '{0}' state changed to {1}.".format(
            unit.uid, state)

        if state == radical.pilot.states.FAILED:
            print "#######################"
            print "##       ERROR       ##"
            print "#######################"
            print "ComputeUnit {0} has FAILED. Can't recover.".format(unit.uid)
            print "ComputeUnit log: {0}".format(unit.log)
            print "STDERR : {0}".format(unit.stderr)
            print "STDOUT : {0}".format(unit.stdout)
            sys.exit(1)

        elif state == radical.pilot.states.CANCELED:
            print "#######################"
            print "##       ERROR       ##"
            print "#######################"
            print "ComputeUnit was canceled prematurely because the pilot was terminated. Can't recover.".format(unit.uid)
            sys.exit(1)

def startPilot(settings):

    session = radical.pilot.Session(database_url="mongodb://ec2-54-221-194-147.compute-1.amazonaws.com:24242/")
    print "Session UID: {0} ".format(session.uid)

    # Add an ssh identity to the sessoion
    if settings.remote_host != "localhost":
        cred = radical.pilot.Context('ssh')
        cred.user_id = settings.uname
        session.add_context(cred)

    # Add a Pilot Manager. Pilot managers manage one or more ComputePilots.
    pmgr = radical.pilot.PilotManager(session=session)
    pmgr.register_callback(pilot_state_cb)

    # Start a pilot at the remote host as per the configs
    pdesc = radical.pilot.ComputePilotDescription()
    pdesc.resource = settings.remote_host
    pdesc.runtime = settings.runtime
    pdesc.cores = settings.cores
    if hasattr(settings,'sandbox'):
        pdesc.sandbox = settings.sandbox
    if settings.remote_host != "localhost":
        pdesc.queue = settings.queue

    # Launch the pilot.
    pilot = pmgr.submit_pilots(pdesc)

    print "Pilot UID       : {0} ".format(pilot.uid)

    umgr = radical.pilot.UnitManager(session=session, scheduler=radical.pilot.SCHED_DIRECT_SUBMISSION)
    # Register our callback with the UnitManager. This callback will get
    # called every time any of the units managed by the UnitManager
    # change their state.
    umgr.register_callback(unit_state_change_cb)

    # Add the previously created ComputePilot to the UnitManager.
    umgr.add_pilots(pilot)

    return umgr, session