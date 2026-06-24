
if __name__ == '__main__':
    import multiprocessing
    multiprocessing.freeze_support()

    from .patator import cli
    cli()


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict