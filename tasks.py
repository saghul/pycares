
import re
from invoke import task

def get_version():
    return re.search(r"""__version__\s+=\s+(?P<quote>['"])(?P<version>.+?)(?P=quote)""", open('src/pycares/_version.py').read()).group('version')

@task
def release(c):
    version = get_version()

    c.run("git tag -a pycares-{0} -m \"pycares {0} release\"".format(version))
    c.run("git push --tags")

    c.run("python setup.py sdist")
    c.run("twine upload dist/pycares-{0}*".format(version))

