
def profile(func):
    from cProfile import Profile
    from functools import wraps
    from tempfile import NamedTemporaryFile

    @wraps(func)
    def profiled_execution(*args, **kwargs):
        logging.info('profiling method %s' % func.__name__)
        profiler = Profile()
        ret = profiler.runcall(func, *args, **kwargs)
        prof_file = NamedTemporaryFile(mode='w',
                                       prefix=func.__name__,
                                       delete=False)
        profiler.dump_stats(prof_file.name)
        logging.info('profiled method %s and dumped results to %s' % (
                     func.__name__, prof_file.name))
        return ret
    return profiled_execution
