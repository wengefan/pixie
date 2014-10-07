from pixie.vm.compiler import compile
from pixie.vm.reader import StringReader, read, eof, PromptReader
from pixie.vm.interpreter import interpret
from rpython.jit.codewriter.policy import JitPolicy
from rpython.rlib.jit import JitHookInterface, Counters
from rpython.annotator.policy import AnnotatorPolicy

import sys


class DebugIFace(JitHookInterface):
    def on_abort(self, reason, jitdriver, greenkey, greenkey_repr, logops, operations):
        print "Aborted Trace, reason: ", Counters.counter_names[reason], logops, greenkey_repr

import sys, pdb

class Policy(JitPolicy, AnnotatorPolicy):
    def __init__(self):
        JitPolicy.__init__(self, DebugIFace())

    #def event(pol, bookkeeper, what, x):
    #    pass

def jitpolicy(driver):
    return JitPolicy(jithookiface=DebugIFace())

def entry_point(foo=None):
    print "Pixie 0.1 - Interactive REPL"
    #try:
    #    code = argv[1]
    #except IndexError:
    #    print "must provide a program"
    #    return 1
    # rdr = StreamReader(sys.stdin)
    # while True:
    #     #val = read(rdr, True)
    #     #if val is eof:
    #     #    break
    #     val = read(StringReader(raw_input("user>")), True)
    #     print interpret(compile(val))
    # interpret(compile(read(StringReader("""
    #                          (do (def foo (fn [h v] (h 42)))
    #                          ((create-stacklet foo) 0))
    # """), True)))
    from pixie.vm.keyword import keyword
    import pixie.vm.rt as rt
    from pixie.vm.string import String
    #rt.load_file(String(u"pixie/stdlib.lisp"))

    rdr = PromptReader()
    while True:
        val = interpret(compile(read(rdr, True)))
        if val is keyword(u"exit-repl"):
            break
        val = rt.str(val)
        assert isinstance(val, String), "str should always return a string"
        print val._str

    return 0

from rpython.rtyper.lltypesystem import lltype
from rpython.jit.metainterp import warmspot

def run_child(glob, loc):
    import sys, pdb
    interp = loc['interp']
    graph = loc['graph']
    interp.malloc_check = False

    def returns_null(T, *args, **kwds):
        return lltype.nullptr(T)
    interp.heap.malloc_nonmovable = returns_null     # XXX

    from rpython.jit.backend.llgraph.runner import LLGraphCPU
    #LLtypeCPU.supports_floats = False     # for now
    apply_jit(interp, graph, LLGraphCPU)


def apply_jit(interp, graph, CPUClass):
    print 'warmspot.jittify_and_run() started...'
    policy = Policy()
    warmspot.jittify_and_run(interp, graph, [], policy=policy,
                             listops=True, CPUClass=CPUClass,
                             backendopt=True, inline=True)

def run_debug(argv):
    from rpython.rtyper.test.test_llinterp import get_interpreter

    # first annotate and rtype
    try:
        interp, graph = get_interpreter(entry_point, [], backendopt=False,
                                        #config=config,
                                        #type_system=config.translation.type_system,
                                        policy=Policy())
    except Exception, e:
        print '%s: %s' % (e.__class__, e)
        pdb.post_mortem(sys.exc_info()[2])
        raise

    # parent process loop: spawn a child, wait for the child to finish,
    # print a message, and restart
    #unixcheckpoint.restartable_point(auto='run')

    from rpython.jit.codewriter.codewriter import CodeWriter
    CodeWriter.debug = True
    run_child(globals(), locals())


def target(*args):
    import pixie.vm.rt as rt
    rt.__config__ = args[0].config
    import pixie.vm.stacklet

    import pixie.vm.rt as rt
    from pixie.vm.string import String
    rt.load_file(String(u"pixie/stdlib.lisp"))


    return entry_point, None

import rpython.config.translationoption
print rpython.config.translationoption.get_combined_translation_config()

if __name__ == "__main__":
    import pixie.vm.rt as rt
    from pixie.vm.string import String
    rt.load_file(String(u"pixie/stdlib.lisp"))
    #run_debug(sys.argv)
    entry_point()