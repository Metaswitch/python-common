import cffi

ffi = cffi.FFI()

ffi.set_source("_cffi",
               """
                #include "namespace_hop.h"
               """,
               libraries=["clearwaterutils", "stdc++"])

ffi.cdef("""
          int create_connection_in_namespace(const char* host, const char* port, const char* socket_factory_path);
          """)

if __name__ == "__main__":
    ffi.compile()
