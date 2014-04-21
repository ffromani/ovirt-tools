import os.path
import tempfile

from fabric.api import run
from fabric.context_managers import cd, quiet
from fabric.operations import put


BUILDROOT = '~/build'


def status():
    for (name, ver, rev, arch) in sorted(find_pkgs()):
        print '%24s: %s-%s (%s)' % (name, ver, rev, arch)


def clean():
    with cd(BUILDROOT):
        run('rm -rf ./vdsm*')


def deploy(tarpath):
    build_dir, tarball = upload(tarpath)
    with cd(build_dir):
        run('tar Jxvf %s' % tarball)
        with cd('vdsm'):
            make()
            rpm()
            with cd('rpm/RPMS'):
                update()


def upload(tarpath):
    run('mkdir -p %s' % BUILDROOT)
    tarball = os.path.basename(tarpath)
    build_dir = tempfile.mktemp(prefix='vdsm', dir=BUILDROOT)
    run('mkdir -p %s' % build_dir)
    put(tarpath, os.path.join(build_dir, tarball))
    return build_dir, tarball


def make():
    run('make distclean')
    run('./autogen.sh')
    run('./configure --prefix=/usr')
    run('make dist')


def rpm():
    rpmdirs()
    run('cp vdsm.spec rpm/SPECS/')
    run('cp vdsm-*.tar.gz rpm/SOURCES/')
    run('rpmbuild -ba --define "_topdir $(pwd)/rpm" rpm/SPECS/vdsm.spec')


def update():
    todo = [ os.path.join(arch, name + '*')
             for (name, ver, rev, arch) in find_pkgs() ]
    run('sudo rpm -Uvh --force %s' % ' '.join(todo))


def find_pkgs():
    with quiet():
        out = run('rpm -qa | grep vdsm')
    for desc in [ line.strip() for line in out.split('\n') ]:
        pkg, tag, arch = desc.rsplit('.', 2)
        name, ver, rev = pkg.rsplit('-', 2)
        yield (name, ver, rev, arch)


def rpmdirs():
    with quiet():
        for subdir in ('BUILD', 'RPMS', 'SRPMS', 'SOURCES', 'SPECS'):
            run('mkdir -p %s' % os.path.join('rpm', subdir))
