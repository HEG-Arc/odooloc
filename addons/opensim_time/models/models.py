import threading

from odoo import fields
from datetime import datetime, timedelta, time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT




class OpensimTime:

    # only one simulation is active/running at at any time for now
    # we use class vars to manage simulationtime_now
    _simulation_start_time = None
    _simulation_end_time = None
    _simulation_min_per_day_rate = 1  # One simulation day passes every 1 minute

    @classmethod
    def reset_start_time(cls, dt=None):
        cls._simulation_start_time = dt or datetime.now()
        cls._simulation_end_time = None

    @classmethod
    def pause(cls,dt=None):
        cls._simulation_end_time = dt or datetime.now()

    @classmethod
    def stop(cls):
        cls._simulation_start_time = None
        cls._simulation_end_time = None

    @classmethod
    def duration(cls):

        if cls._simulation_start_time:
            simulation_now = datetime.now()
            simulation_time = (cls._simulation_end_time or simulation_now) - cls._simulation_start_time
            return simulation_time
        else:
            return timedelta(0)

    @classmethod
    def now(cls):
        # simulation time datetime.now like (but for tz support)
        return datetime.now() + timedelta(days=cls.duration().seconds // (60 * cls._simulation_min_per_day_rate))



    @classmethod
    def today(cls):
        # simulation time date.today like
        return cls.now().date()

    @classmethod
    def until_tomorrow(cls):
        """
        :return: time left until simulation date change in second
        """
        simulation_now = datetime.now()
        if cls._simulation_start_time:
            # active simulation case
            if cls._simulation_end_time:
                time_left = threading.TIMEOUT_MAX
            else:
                simulation_time = (cls._simulation_end_time or simulation_now) - cls._simulation_start_time
                time_left = (60 * cls._simulation_min_per_day_rate) - simulation_time.seconds % (
                            60 * cls._simulation_min_per_day_rate)
        else:
            # real time case
            tomorrow = simulation_now + timedelta(days=1)
            time_left = (datetime.combine(tomorrow, time.min) - simulation_now).seconds
        return time_left


def simulationtime_now(*args):
    """ Define our own datetime.now to replace odoo's fields.Datetime.now static method that
        is used in all modules to get current date.

        Return the current Simulation's day and time in the format expected by the ORM.
        This function may be used to compute default values.
    """
    return OpensimTime.now().strftime(DATETIME_FORMAT)

# found nice monkey patching decorator in odoo base_sparse_field models
def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """
    def decorate(func):
        name = func.__name__
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate

@monkey_patch(fields.Datetime)
def now(*args):
    return OpensimTime.now().strftime(DATETIME_FORMAT)


# Here we patch Odoo Datetime static method
#fields.Datetime.now = simulationtime_now


@monkey_patch(fields.Date)
def today(*args):
    """ Return the current day in the format expected by the ORM.
        This function may be used to compute default values.
    """
    return OpensimTime.today().strftime(DATE_FORMAT)

@monkey_patch(fields.Date)
def context_today(record, timestamp=None):
    if timestamp is None:
        timestamp = OpensimTime.now()
    return context_today.super(record, timestamp)
