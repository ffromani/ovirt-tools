import os.path
import tempfile

from fabric.api import run
from fabric.context_managers import cd, quiet, hide
from fabric.operations import put
from fabric.decorators import task


BUILDROOT = '~/build'


@task
def status():
    pkgs = find_pkgs()
    if pkgs:
        for (name, ver, rev, arch) in sorted(pkgs):
            print '%24s: %s-%s (%s)' % (name, ver, rev, arch)
    else:
        print 'VDSM not installed'


@task
def clean():
    with cd(BUILDROOT):
        run('rm -rf ./vdsm*')

@task
def vdeploy(tarpath):
    build_dir, tarball = upload(tarpath)
    with cd(build_dir):
        run('tar Jxvf %s' % tarball)
        with cd('vdsm'):
            make()
            rpm()
            with cd('rpm/RPMS'):
                update()

@task
def deploy(tarpath):
    with hide('stdout'):
        vdeploy(tarpath)

def clearlog(target):
    if target in ('supervdsmd', 'vdsmd'):
        run('sudo truncate -s 0 /var/log/vdsm/%s.log' % (target))


def service(target, action):
    if (target in ('sanlock', 'supervdsmd', 'vdsmd', 'libvirtd') and
        action in ('stop', 'start', 'restart', 'status')):
        run('sudo service %s %s' % (target, action))


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
    pkgs = find_pkgs()
    if not pkgs:
        # default
        pkgs = [('vdsm', None, None, 'x86_64'),
                ('vdsm-python', None, None, 'x86_64'),
                ('vdsm-api', None, None, 'noarch'),
                ('vdsm-xmlrpc', None, None, 'noarch'),
                ('vdsm-cli', None, None, 'noarch'),
                ('vdsm-python-zombiereaper', None, None, 'noarch')]
    run('sudo rpm -Uvh --force %s' % ' '.join(
        os.path.join(arch, name + '*') for (name, ver, rev, arch) in pkgs))


def find_pkgs():
    with quiet():
        out = run('rpm -qa | grep vdsm')
    res = []
    for desc in [ line.strip() for line in out.split('\n') ]:
        try:
            pkg, tag, arch = desc.rsplit('.', 2)
            name, ver, rev = pkg.rsplit('-', 2)
            res.append((name, ver, rev, arch))
        except (IndexError, ValueError):
            return []
    return res


def rpmdirs():
    with quiet():
        for subdir in ('BUILD', 'RPMS', 'SRPMS', 'SOURCES', 'SPECS'):
            run('mkdir -p %s' % os.path.join('rpm', subdir))
