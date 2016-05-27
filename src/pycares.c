
#include "pycares.h"

#include "cares.c"
#include "errno.c"


/* adapted from ares_gethostbyaddr.c */
static PyObject *
pycares_func_reverse_address(PyObject *obj, PyObject *args)
{
    char *ip_address;
    char name[128];
    unsigned long laddr, a1, a2, a3, a4;
    unsigned char *bytes;
    struct in_addr addr4;
    struct in6_addr addr6;

    if (!PyArg_ParseTuple(args, "s:reverse_address", &ip_address)) {
        return NULL;
    }

    if (ares_inet_pton(AF_INET, ip_address, &addr4) == 1) {
       laddr = ntohl(addr4.s_addr);
       a1 = (laddr >> 24UL) & 0xFFUL;
       a2 = (laddr >> 16UL) & 0xFFUL;
       a3 = (laddr >>  8UL) & 0xFFUL;
       a4 = laddr & 0xFFUL;
       sprintf(name, "%lu.%lu.%lu.%lu.in-addr.arpa", a4, a3, a2, a1);
    } else if (ares_inet_pton(AF_INET6, ip_address, &addr6) == 1) {
       bytes = (unsigned char *)&addr6;
       /* There are too many arguments to do this in one line using
        * minimally C89-compliant compilers */
       sprintf(name,
                "%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.",
                bytes[15]&0xf, bytes[15] >> 4, bytes[14]&0xf, bytes[14] >> 4,
                bytes[13]&0xf, bytes[13] >> 4, bytes[12]&0xf, bytes[12] >> 4,
                bytes[11]&0xf, bytes[11] >> 4, bytes[10]&0xf, bytes[10] >> 4,
                bytes[9]&0xf, bytes[9] >> 4, bytes[8]&0xf, bytes[8] >> 4);
       sprintf(name+strlen(name),
                "%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.%x.ip6.arpa",
                bytes[7]&0xf, bytes[7] >> 4, bytes[6]&0xf, bytes[6] >> 4,
                bytes[5]&0xf, bytes[5] >> 4, bytes[4]&0xf, bytes[4] >> 4,
                bytes[3]&0xf, bytes[3] >> 4, bytes[2]&0xf, bytes[2] >> 4,
                bytes[1]&0xf, bytes[1] >> 4, bytes[0]&0xf, bytes[0] >> 4);
    } else {
        PyErr_SetString(PyExc_ValueError, "invalid IP address");
        return NULL;
    }

    return Py_BuildValue("s", name);
}


static PyMethodDef
pycares_methods[] = {
    { "reverse_address", (PyCFunction)pycares_func_reverse_address, METH_VARARGS, "Get reverse representation of an IP address" },
    { NULL }
};


#ifdef PYCARES_PYTHON3
static PyModuleDef pycares_module = {
    PyModuleDef_HEAD_INIT,
    "pycares._core",        /*m_name*/
    NULL,                   /*m_doc*/
    -1,                     /*m_size*/
    pycares_methods,        /*m_methods*/
};
#endif


/* Module */
PyObject *
init_pycares(void)
{
    /* Modules */
    PyObject *pycares;
    PyObject *errno_module;

    /* Main module */
#ifdef PYCARES_PYTHON3
    pycares = PyModule_Create(&pycares_module);
#else
    pycares = Py_InitModule("pycares._core", pycares_methods);
#endif

    /* Errno module */
    errno_module = init_errno();
    if (errno_module == NULL) {
        goto fail;
    }
    PyCaresModule_AddObject(pycares, "errno", errno_module);
#ifdef PYCARES_PYTHON3
    PyDict_SetItemString(PyImport_GetModuleDict(), pycares_errorno_module.m_name, errno_module);
    Py_DECREF(errno_module);
#endif

    /* Exceptions */
    PyExc_AresError = PyErr_NewException("pycares.AresError", NULL, NULL);
    PyCaresModule_AddType(pycares, "AresError", (PyTypeObject *)PyExc_AresError);

    /* Initialize PyStructSequence types */
    if (AresHostResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresHostResultType, &ares_host_result_desc);
        PyCaresModule_AddType(pycares, "ares_host_result", &AresHostResultType);
    }
    if (AresNameinfoResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresNameinfoResultType, &ares_nameinfo_result_desc);
        PyCaresModule_AddType(pycares, "ares_nameinfo_result", &AresNameinfoResultType);
    }
    if (AresQuerySimpleResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQuerySimpleResultType, &ares_query_simple_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_simple_result", &AresQuerySimpleResultType);
    }
    if (AresQueryCNAMEResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQueryCNAMEResultType, &ares_query_cname_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_cname_result", &AresQueryCNAMEResultType);
    }
    if (AresQueryMXResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQueryMXResultType, &ares_query_mx_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_mx_result", &AresQueryMXResultType);
    }
    if (AresQueryNSResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQueryNSResultType, &ares_query_ns_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_ns_result", &AresQueryNSResultType);
    }
    if (AresQueryPTRResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQueryPTRResultType, &ares_query_ptr_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_ptr_result", &AresQueryPTRResultType);
    }
    if (AresQuerySOAResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQuerySOAResultType, &ares_query_soa_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_soa_result", &AresQuerySOAResultType);
    }
    if (AresQuerySRVResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQuerySRVResultType, &ares_query_srv_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_srv_result", &AresQuerySRVResultType);
    }
    if (AresQueryTXTResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQueryTXTResultType, &ares_query_txt_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_txt_result", &AresQueryTXTResultType);
    }
    if (AresQueryNAPTRResultType.tp_name == 0) {
        PyStructSequence_InitType(&AresQueryNAPTRResultType, &ares_query_naptr_result_desc);
        PyCaresModule_AddType(pycares, "ares_query_naptr_result", &AresQueryNAPTRResultType);
    }

    /* Flag values */
    PyModule_AddIntMacro(pycares, ARES_FLAG_USEVC);
    PyModule_AddIntMacro(pycares, ARES_FLAG_PRIMARY);
    PyModule_AddIntMacro(pycares, ARES_FLAG_IGNTC);
    PyModule_AddIntMacro(pycares, ARES_FLAG_NORECURSE);
    PyModule_AddIntMacro(pycares, ARES_FLAG_STAYOPEN);
    PyModule_AddIntMacro(pycares, ARES_FLAG_NOSEARCH);
    PyModule_AddIntMacro(pycares, ARES_FLAG_NOALIASES);
    PyModule_AddIntMacro(pycares, ARES_FLAG_NOCHECKRESP);

    /* Nameinfo flag values */
    PyModule_AddIntMacro(pycares, ARES_NI_NOFQDN);
    PyModule_AddIntMacro(pycares, ARES_NI_NUMERICHOST);
    PyModule_AddIntMacro(pycares, ARES_NI_NAMEREQD);
    PyModule_AddIntMacro(pycares, ARES_NI_NUMERICSERV);
    PyModule_AddIntMacro(pycares, ARES_NI_DGRAM);
    PyModule_AddIntMacro(pycares, ARES_NI_TCP);
    PyModule_AddIntMacro(pycares, ARES_NI_UDP);
    PyModule_AddIntMacro(pycares, ARES_NI_SCTP);
    PyModule_AddIntMacro(pycares, ARES_NI_DCCP);
    PyModule_AddIntMacro(pycares, ARES_NI_NUMERICSCOPE);
    PyModule_AddIntMacro(pycares, ARES_NI_LOOKUPHOST);
    PyModule_AddIntMacro(pycares, ARES_NI_LOOKUPSERVICE);
    PyModule_AddIntMacro(pycares, ARES_NI_IDN);
    PyModule_AddIntMacro(pycares, ARES_NI_IDN_ALLOW_UNASSIGNED);
    PyModule_AddIntMacro(pycares, ARES_NI_IDN_USE_STD3_ASCII_RULES);

    /* Bad socket */
    PyModule_AddIntMacro(pycares, ARES_SOCKET_BAD);

    /* Query types */
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_A", T_A);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_AAAA", T_AAAA);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_CNAME", T_CNAME);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_MX", T_MX);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_NAPTR", T_NAPTR);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_NS", T_NS);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_PTR", T_PTR);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_SOA", T_SOA);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_SRV", T_SRV);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_TXT", T_TXT);

    PyCaresModule_AddType(pycares, "Channel", &ChannelType);

    /* c-ares version */
    PyModule_AddStringConstant(pycares, "ARES_VERSION", ares_version(NULL));

    return pycares;

fail:
#ifdef PYCARES_PYTHON3
    Py_DECREF(pycares);
#endif
    return NULL;

}


#ifdef PYCARES_PYTHON3
PyMODINIT_FUNC
PyInit__core(void)
{
    return init_pycares();
}
#else
PyMODINIT_FUNC
init_core(void)
{
    init_pycares();
}
#endif

