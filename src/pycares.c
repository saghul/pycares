
#include "pycares.h"

#include "cares.c"
#include "errno.c"


static void
_ares_cleanup(void)
{
    if (ares_lib_initialized) {
        ares_library_cleanup();
    }
}


#ifdef PYCARES_PYTHON3
static PyModuleDef pycares_module = {
    PyModuleDef_HEAD_INIT,
    "pycares",              /*m_name*/
    NULL,                   /*m_doc*/
    -1,                     /*m_size*/
    NULL,                   /*m_methods*/
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
    pycares = Py_InitModule("pycares", NULL);
#endif

    /* Errno module */
    errno_module = init_errno();
    if (errno_module == NULL) {
        goto fail;
    }
    PyCaresModule_AddObject(pycares, "errno", errno_module);

    /* Cleanup ares on exit */
    Py_AtExit(_ares_cleanup);

    /* Initialize PyStructSequence types */
    if (AresHostResultType.tp_name == 0)
        PyStructSequence_InitType(&AresHostResultType, &ares_host_result_desc);
    if (AresNameinfoResultType.tp_name == 0)
        PyStructSequence_InitType(&AresNameinfoResultType, &ares_nameinfo_result_desc);
    if (AresQueryMXResultType.tp_name == 0)
        PyStructSequence_InitType(&AresQueryMXResultType, &ares_query_mx_result_desc);
    if (AresQuerySOAResultType.tp_name == 0)
        PyStructSequence_InitType(&AresQuerySOAResultType, &ares_query_soa_result_desc);
    if (AresQuerySRVResultType.tp_name == 0)
        PyStructSequence_InitType(&AresQuerySRVResultType, &ares_query_srv_result_desc);
    if (AresQueryNAPTRResultType.tp_name == 0)
        PyStructSequence_InitType(&AresQueryNAPTRResultType, &ares_query_naptr_result_desc);

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
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_SOA", T_SOA);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_SRV", T_SRV);
    PyModule_AddIntConstant(pycares, "QUERY_TYPE_TXT", T_TXT);

    PyCaresModule_AddType(pycares, "Channel", &ChannelType);

    /* Module version (the MODULE_VERSION macro is defined by setup.py) */
    PyModule_AddStringConstant(pycares, "__version__", __MSTR(MODULE_VERSION));

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
PyInit_pycares(void)
{
    return init_pycares();
}
#else
PyMODINIT_FUNC
initpycares(void)
{
    init_pycares();
}
#endif


