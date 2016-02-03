"""
A script to generate the schemas for the GA4GH protocol. These are generated
from a copy of the Protocol Buffers schema and use it to generate
the Python class definitions in proto/. These are also stored in revision
control to aid Travis building.
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import os
import os.path
import subprocess
import fnmatch
import re
import argparse


class ProtobufGenerator(object):
    def __init__(self, version):
        self.version = version

    def run(self, args):
        script_path = os.path.dirname(os.path.realpath(__file__))
        server = os.path.realpath(os.path.join(script_path, ".."))
        schemas = os.path.join(server, args.schema_path)

        if not os.path.exists(schemas):
            raise Exception(
                "Can't find schemas folder. " +
                "Thought it would be at %s" % os.path.realpath(schemas))

        src = os.path.realpath(os.path.join(schemas, "src/main/resources"))

        if not os.path.exists(os.path.join(server, "proto")):
            raise Exception(
                "Can't find destination python directory %s"
                % os.path.realpath(os.path.join(server, "proto")))

        if not os.path.exists(src):
            raise Exception(
                "Can't find source proto directory %s" % os.path.realpath(src))

        def find_in_path(cmd):
            PATH = os.environ.get("PATH", os.defpath).split(os.pathsep)
            for x in PATH:
                possible = os.path.join(x, cmd)
                if os.path.exists(possible):
                    return possible
            return None

        # From http://stackoverflow.com/a/1714190/320546
        def version_compare(version1, version2):
            def normalize(v):
                return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
            return cmp(normalize(version1), normalize(version2))

        protocs = [
            os.path.realpath(x) for x in
            "%s/protobuf/src/protoc" % server,
            find_in_path("protoc")
            if x is not None]
        protoc = None
        for c in protocs:
            if not os.path.exists(c):
                continue
            output = subprocess.check_output([c, "--version"]).strip()
            try:
                (lib, version) = output.split(" ")
                if lib != "libprotoc":
                    raise Exception("lib didn't match 'libprotoc'")
                if version_compare("3.0.0", version) > 0:
                    raise Exception("version < 3.0.0")
                protoc = c
                break

            except Exception:
                print (
                    "Not using {path} because it returned " +
                    "'{version}' rather than \"libprotoc <version>\", where " +
                    "<version> >= 3.0.0").format(path=c, format=output)

        if protoc is None:
            raise Exception("Can't find a good protoc. Tried %s" % protocs)
        print ("Using %s for protoc" % protoc)

        protos = []
        for root, dirs, files in os.walk(src):
            protos.extend([
                os.path.join(root, f)
                for f in fnmatch.filter(files, "*.proto")])
        if len(protos) == 0:
            raise Exception("Didn't find any proto files in %s" % src)
        cmd = "{protoc} -I {src} --python_out={server} {proto_files}".format(
            protoc=protoc, src=src,
            server=server, proto_files=" ".join(protos))
        os.system(cmd)

        proto_folder = os.path.join(server, "proto")
        for root, dirs, files in os.walk(proto_folder):
            print ("Creating __init__.py in %s" % root)
            with file(os.path.join(root, "__init__.py"), "w") as f:
                if root == proto_folder:
                    f.write("version = '%s'" % self.version)


def main():
    parser = argparse.ArgumentParser(
        description="Script to process GA4GH Protocol buffer schemas")
    parser.add_argument(
        "version", help="Version number of the schema we're compiling")
    parser.add_argument(
        "--schema-path", default="../schemas",
        help="Path to schemas. Default is ../schemas")
    args = parser.parse_args()
    pb = ProtobufGenerator(args.version)
    pb.run(args)

if __name__ == "__main__":
    main()
