
/* Borrowed code from Python (Modules/errnomodule.c) */

static void
inscode(PyObject *module_dict, PyObject *other_dict, const char *name, int code)
{
    PyObject *error_name = Py_BuildValue("s", name);
    PyObject *error_code = PyInt_FromLong((long) code);

    /* Don't bother checking for errors; they'll be caught at the end
     * of the module initialization function by the caller of
     * init_errno().
     */
    if (error_name && error_code) {
        PyDict_SetItem(module_dict, error_name, error_code);
        PyDict_SetItem(other_dict, error_code, error_name);
    }
    Py_XDECREF(error_name);
    Py_XDECREF(error_code);
}


static PyObject *
Errno_func_strerror(PyObject *obj, PyObject *args)
{
    int errorno;

    UNUSED_ARG(obj);

    if (!PyArg_ParseTuple(args, "i:strerror", &errorno)) {
        return NULL;
    }

    return Py_BuildValue("s", ares_strerror(errorno));
}


static PyMethodDef
Errno_methods[] = {
    { "strerror", (PyCFunction)Errno_func_strerror, METH_VARARGS, "Get string representation of a c-ares error code." },
    { NULL }
};


#ifdef PYCARES_PYTHON3
static PyModuleDef pycares_errorno_module = {
    PyModuleDef_HEAD_INIT,
    "pycares._core.errno",  /*m_name*/
    NULL,                   /*m_doc*/
    -1,                     /*m_size*/
    Errno_methods,          /*m_methods*/
};
#endif

PyObject *
init_errno(void)
{
    PyObject *module;
    PyObject *module_dict;
    PyObject *errorcode_dict;
#ifdef PYCARES_PYTHON3
    module = PyModule_Create(&pycares_errorno_module);
#else
    module = Py_InitModule("pycares._core.errno", Errno_methods);
#endif
    if (module == NULL) {
        return NULL;
    }

    module_dict = PyModule_GetDict(module);
    errorcode_dict = PyDict_New();
    if (!module_dict || !errorcode_dict || PyDict_SetItemString(module_dict, "errorcode", errorcode_dict) < 0) {
        return NULL;
    }

#define XX(name) inscode(module_dict, errorcode_dict, __STRING(ARES_##name), ARES_##name);
    XX(SUCCESS)
    XX(ENODATA)
    XX(EFORMERR)
    XX(ESERVFAIL)
    XX(ENOTFOUND)
    XX(ENOTIMP)
    XX(EREFUSED)
    XX(EBADQUERY)
    XX(EBADNAME)
    XX(EBADFAMILY)
    XX(EBADRESP)
    XX(ECONNREFUSED)
    XX(ETIMEOUT)
    XX(EOF)
    XX(EFILE)
    XX(ENOMEM)
    XX(EDESTRUCTION)
    XX(EBADSTR)
    XX(EBADFLAGS)
    XX(ENONAME)
    XX(EBADHINTS)
    XX(ENOTINITIALIZED)
    XX(ELOADIPHLPAPI)
    XX(EADDRGETNETWORKPARAMS)
    XX(ECANCELLED)
#undef XX

    Py_DECREF(errorcode_dict);

    return module;
}

