
#ifndef PYCARES_H
#define PYCARES_H

/* python */
#define PY_SSIZE_T_CLEAN
#include "Python.h"
#include "structmember.h"
#include "structseq.h"

/* Python3 */
#if PY_MAJOR_VERSION >= 3
    #define PYCARES_PYTHON3
    #define PyInt_FromLong PyLong_FromLong
    #define PyString_FromString PyUnicode_FromString
#endif

/* c-ares */
#define CARES_STATICLIB 1
#include "ares.h"

/* Custom types */
typedef int Bool;
#define True  1
#define False 0

/* Utility macros */
#ifndef __STRING
    #define __STRING(x) #x
#endif
#define __MSTR(x) __STRING(x)

#define UNUSED_ARG(arg)  (void)arg

#if defined(__MINGW32__) || defined(_MSC_VER)
    #define PYCARES_WINDOWS
#endif

#define ASSERT(x)                                                           \
    do {                                                                    \
        if (!(x)) {                                                         \
            fprintf (stderr, "%s:%u: %s: Assertion `" #x "' failed.\n",     \
                     __FILE__, __LINE__, __func__);                         \
            abort();                                                        \
        }                                                                   \
    } while(0)                                                              \

#ifdef PYCARES_WINDOWS
    #include <inet_net_pton.h>
    #include <inet_ntop.h>
    #define pycares_inet_pton ares_inet_pton
    #define pycares_inet_ntop ares_inet_ntop
#else /* __POSIX__ */
    #include <arpa/inet.h>
    #define pycares_inet_pton inet_pton
    #define pycares_inet_ntop inet_ntop
#endif

#define CHECK_CHANNEL(ch)                                                           \
    do {                                                                            \
        if (!ch->channel) {                                                         \
            PyErr_SetString(PyExc_AresError, "Channel has already been destroyed"); \
            return NULL;                                                            \
        }                                                                           \
    } while(0)                                                                      \

#define RAISE_ARES_EXCEPTION(code)                                                  \
    do {                                                                            \
        PyObject *exc_data = Py_BuildValue("(is)", code, ares_strerror(code));      \
        if (exc_data != NULL) {                                                     \
            PyErr_SetObject(PyExc_AresError, exc_data);                             \
            Py_DECREF(exc_data);                                                    \
        }                                                                           \
    } while(0)                                                                      \


/* Python types */
typedef struct {
    PyObject_HEAD
    PyObject *sock_state_cb;
    ares_channel channel;
} Channel;

static PyTypeObject ChannelType;

static PyTypeObject AresHostResultType;

static PyStructSequence_Field ares_host_result_fields[] = {
    {"name", ""},
    {"aliases", ""},
    {"addresses", ""},
    {NULL}
};

static PyStructSequence_Desc ares_host_result_desc = {
    "ares_host_result",
    NULL,
    ares_host_result_fields,
    3
};

static PyTypeObject AresNameinfoResultType;

static PyStructSequence_Field ares_nameinfo_result_fields[] = {
    {"node", ""},
    {"service", ""},
    {NULL}
};

static PyStructSequence_Desc ares_nameinfo_result_desc = {
    "ares_nameinfo_result",
    NULL,
    ares_nameinfo_result_fields,
    2
};

static PyTypeObject AresQueryMXResultType;

static PyStructSequence_Field ares_query_mx_result_fields[] = {
    {"host", ""},
    {"priority", ""},
    {NULL}
};

static PyStructSequence_Desc ares_query_mx_result_desc = {
    "ares_query_mx_result",
    NULL,
    ares_query_mx_result_fields,
    2
};

static PyTypeObject AresQuerySOAResultType;

static PyStructSequence_Field ares_query_soa_result_fields[] = {
    {"nsname", ""},
    {"hostmaster", ""},
    {"serial", ""},
    {"refresh", ""},
    {"retry", ""},
    {"expires", ""},
    {"minttl", ""},
    {NULL}
};

static PyStructSequence_Desc ares_query_soa_result_desc = {
    "ares_query_soa_result",
    NULL,
    ares_query_soa_result_fields,
    7
};

static PyTypeObject AresQuerySRVResultType;

static PyStructSequence_Field ares_query_srv_result_fields[] = {
    {"host", ""},
    {"port", ""},
    {"priority", ""},
    {"weight", ""},
    {NULL}
};

static PyStructSequence_Desc ares_query_srv_result_desc = {
    "ares_query_srv_result",
    NULL,
    ares_query_srv_result_fields,
    4
};

static PyTypeObject AresQueryNAPTRResultType;

static PyStructSequence_Field ares_query_naptr_result_fields[] = {
    {"order", ""},
    {"preference", ""},
    {"flags", ""},
    {"service", ""},
    {"regex", ""},
    {"replacement", ""},
    {NULL}
};

static PyStructSequence_Desc ares_query_naptr_result_desc = {
    "ares_query_naptr_result",
    NULL,
    ares_query_naptr_result_fields,
    6
};


/* Some helper stuff */

/* Add a type to a module */
static int
PyCaresModule_AddType(PyObject *module, const char *name, PyTypeObject *type)
{
    if (PyType_Ready(type)) {
        return -1;
    }
    Py_INCREF(type);
    if (PyModule_AddObject(module, name, (PyObject *)type)) {
        Py_DECREF(type);
        return -1;
    }
    return 0;
}

/* Add a type to a module */
static int
PyCaresModule_AddObject(PyObject *module, const char *name, PyObject *value)
{
    Py_INCREF(value);
    if (PyModule_AddObject(module, name, value)) {
        Py_DECREF(value);
        return -1;
    }
    return 0;
}


#endif

