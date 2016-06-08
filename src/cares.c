
#ifdef PYCARES_WINDOWS
    #include <winsock.h>
    #include <winsock2.h>
#else /* __POSIX__ */
    #include <arpa/inet.h>
    #include <netdb.h>
#endif
#include "nameser.h"
#include "bytesobject.h"

#define PYCARES_ADDRTTL_SIZE 256


static PyObject* PyExc_AresError;


/* Helpers borrowed from libuv */
struct sockaddr_in uv_ip4_addr(const char* ip, int port) {
    struct sockaddr_in addr;

    memset(&addr, 0, sizeof(struct sockaddr_in));

    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    ares_inet_pton(AF_INET, ip, &addr.sin_addr.s_addr);

    return addr;
}

struct sockaddr_in6 uv_ip6_addr(const char* ip, int port) {
    struct sockaddr_in6 addr;

    memset(&addr, 0, sizeof(struct sockaddr_in6));

    addr.sin6_family = AF_INET6;
    addr.sin6_port = htons(port);
    ares_inet_pton(AF_INET6, ip, &addr.sin6_addr);

    return addr;
}


static void
ares__sock_state_cb(void *data, ares_socket_t socket_fd, int readable, int writable)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    Channel *self;
    PyObject *result, *fd, *py_readable, *py_writable;

    self = (Channel *)data;
    ASSERT(self);
    /* Object could go out of scope in the callback, increase refcount to avoid it */
    Py_INCREF(self);

    fd = PyInt_FromLong((long)socket_fd);
    py_readable = PyBool_FromLong((long)readable);
    py_writable = PyBool_FromLong((long)writable);

    result = PyObject_CallFunctionObjArgs(self->sock_state_cb, fd, py_readable, py_writable, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(self->sock_state_cb);
    }
    Py_XDECREF(result);
    Py_DECREF(fd);
    Py_DECREF(py_readable);
    Py_DECREF(py_writable);

    Py_DECREF(self);
    PyGILState_Release(gstate);
}


static void
query_a_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    char ip[INET6_ADDRSTRLEN];
    int i;
    struct ares_addrttl addrttls[PYCARES_ADDRTTL_SIZE];
    int naddrttls = PYCARES_ADDRTTL_SIZE;
    PyObject *dns_result, *errorno, *tmp, *result, *callback;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_a_reply(answer_buf, answer_len, NULL, addrttls, &naddrttls);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyList_New(0);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    for (i = 0; i < naddrttls; i++) {
        ares_inet_ntop(AF_INET, &addrttls[i].ipaddr, ip, sizeof(ip));
        tmp = PyStructSequence_New(&AresQuerySimpleResultType);
        if (tmp == NULL) {
            break;
        }
        PyStructSequence_SET_ITEM(tmp, 0, Py_BuildValue("s", ip));
        PyStructSequence_SET_ITEM(tmp, 1, PyInt_FromLong((long)addrttls[i].ttl));
        PyList_Append(dns_result, tmp);
        Py_DECREF(tmp);
    }
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    Py_DECREF(callback);

    PyGILState_Release(gstate);
}


static void
query_aaaa_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    char ip[INET6_ADDRSTRLEN];
    int i;
    struct ares_addr6ttl addrttls[PYCARES_ADDRTTL_SIZE];
    int naddrttls = PYCARES_ADDRTTL_SIZE;
    PyObject *dns_result, *errorno, *tmp, *result, *callback;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_aaaa_reply(answer_buf, answer_len, NULL, addrttls, &naddrttls);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyList_New(0);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    for (i = 0; i < naddrttls; i++) {
        ares_inet_ntop(AF_INET6, &addrttls[i].ip6addr, ip, sizeof(ip));
        tmp = PyStructSequence_New(&AresQuerySimpleResultType);
        if (tmp == NULL) {
            break;
        }
        PyStructSequence_SET_ITEM(tmp, 0, Py_BuildValue("s", ip));
        PyStructSequence_SET_ITEM(tmp, 1, PyInt_FromLong((long)addrttls[i].ttl));
        PyList_Append(dns_result, tmp);
        Py_DECREF(tmp);
    }
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    Py_DECREF(callback);

    PyGILState_Release(gstate);
}


static void
query_cname_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    struct hostent *hostent = NULL;
    PyObject *dns_result, *errorno, *result, *callback;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_a_reply(answer_buf, answer_len, &hostent, NULL, NULL);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyStructSequence_New(&AresQueryCNAMEResultType);
    PyStructSequence_SET_ITEM(dns_result, 0, Py_BuildValue("s", hostent->h_name));
    /* TODO: add (real) TTL */
    PyStructSequence_SET_ITEM(dns_result, 1, Py_None);
    Py_INCREF(Py_None);
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (hostent) {
        ares_free_hostent(hostent);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
query_mx_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    struct ares_mx_reply *mx_reply, *mx_ptr;
    PyObject *dns_result, *errorno, *tmp, *result, *callback;

    mx_reply = NULL;
    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_mx_reply(answer_buf, answer_len, &mx_reply);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyList_New(0);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    for (mx_ptr = mx_reply; mx_ptr != NULL; mx_ptr = mx_ptr->next) {
        tmp = PyStructSequence_New(&AresQueryMXResultType);
        if (tmp == NULL) {
            break;
        }
        PyStructSequence_SET_ITEM(tmp, 0, Py_BuildValue("s", mx_ptr->host));
        PyStructSequence_SET_ITEM(tmp, 1, PyInt_FromLong((long)mx_ptr->priority));
        PyStructSequence_SET_ITEM(tmp, 2, PyInt_FromLong((long)mx_ptr->ttl));
        PyList_Append(dns_result, tmp);
        Py_DECREF(tmp);
    }
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (mx_reply) {
        ares_free_data(mx_reply);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
query_ns_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    char **ptr;
    struct hostent *hostent = NULL;
    PyObject *dns_result, *errorno, *tmp, *result, *callback;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_ns_reply(answer_buf, answer_len, &hostent);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyList_New(0);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    for (ptr = hostent->h_aliases; *ptr != NULL; ptr++) {
        tmp = PyStructSequence_New(&AresQueryNSResultType);
        if (tmp == NULL) {
            break;
        }
        PyStructSequence_SET_ITEM(tmp, 0, Py_BuildValue("s", *ptr));
        /* TODO: add (real) TTL */
        PyStructSequence_SET_ITEM(tmp, 1, Py_None);
        Py_INCREF(Py_None);
        PyList_Append(dns_result, tmp);
        Py_DECREF(tmp);
    }
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (hostent) {
        ares_free_hostent(hostent);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
query_ptr_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    struct hostent *hostent = NULL;
    PyObject *dns_result, *errorno, *result, *callback;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    /* addr is only used to populate the hostent struct, it's not used to validate the response */
    parse_status = ares_parse_ptr_reply(answer_buf, answer_len, NULL, 0, AF_UNSPEC, &hostent);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyStructSequence_New(&AresQueryPTRResultType);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    PyStructSequence_SET_ITEM(dns_result, 0, Py_BuildValue("s", hostent->h_name));
    /* TODO: add (real) TTL */
    PyStructSequence_SET_ITEM(dns_result, 1, Py_None);
    Py_INCREF(Py_None);
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (hostent) {
        ares_free_hostent(hostent);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
query_txt_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    struct ares_txt_ext *txt_reply, *txt_ptr;
    PyObject *dns_result, *errorno, *tmp_obj, *result, *callback;
    PyObject *assembled_txt;

    txt_reply = NULL;
    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_txt_reply_ext(answer_buf, answer_len, &txt_reply);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyList_New(0);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    tmp_obj = NULL;
    assembled_txt = NULL;
    txt_ptr = txt_reply;
    while (1) {
        if (txt_ptr == NULL || txt_ptr->record_start == 1) {
            if (tmp_obj != NULL) {
                /* Add the assembled record to the result when seeing a new record (except for the first time) and after the last chunk has been seen */
                PyStructSequence_SET_ITEM(tmp_obj, 0, Py_BuildValue("s", PyBytes_AS_STRING(assembled_txt)));
                PyList_Append(dns_result, tmp_obj);
                Py_DECREF(tmp_obj);
                Py_DECREF(assembled_txt);
            }
            if (txt_ptr == NULL) {
                /* Exit while loop when last chunk has been seen */
                break;
            }
        }
        if (txt_ptr->record_start == 1) {
            /* In case of a new record, prepare its object */
            tmp_obj = PyStructSequence_New(&AresQueryTXTResultType);
            if (tmp_obj == NULL) {
                break;
            }
            /* ttl of the first chunk is representative for the entire record */
            PyStructSequence_SET_ITEM(tmp_obj, 1, PyInt_FromLong((long)txt_ptr->ttl));
            assembled_txt = PyBytes_FromString("");
        }
        /* Concatenate each chunk's text onto the assembled record */
        PyBytes_ConcatAndDel(&assembled_txt, PyBytes_FromString((char*)txt_ptr->txt));
        if (assembled_txt == NULL) {
            Py_DECREF(tmp_obj);
            break;
        }
        /* Move on to the next chunk */
        txt_ptr = txt_ptr->next;
    }

    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (txt_reply) {
        ares_free_data(txt_reply);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
query_soa_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    struct ares_soa_reply *soa_reply = NULL;
    PyObject *dns_result, *errorno, *result, *callback;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_soa_reply(answer_buf, answer_len, &soa_reply);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyStructSequence_New(&AresQuerySOAResultType);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    PyStructSequence_SET_ITEM(dns_result, 0, Py_BuildValue("s", soa_reply->nsname));
    PyStructSequence_SET_ITEM(dns_result, 1, Py_BuildValue("s", soa_reply->hostmaster));
    PyStructSequence_SET_ITEM(dns_result, 2, PyInt_FromLong((long)soa_reply->serial));
    PyStructSequence_SET_ITEM(dns_result, 3, PyInt_FromLong((long)soa_reply->refresh));
    PyStructSequence_SET_ITEM(dns_result, 4, PyInt_FromLong((long)soa_reply->retry));
    PyStructSequence_SET_ITEM(dns_result, 5, PyInt_FromLong((long)soa_reply->expire));
    PyStructSequence_SET_ITEM(dns_result, 6, PyInt_FromLong((long)soa_reply->minttl));
    PyStructSequence_SET_ITEM(dns_result, 7, PyInt_FromLong((long)soa_reply->ttl));

    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (soa_reply) {
        ares_free_data(soa_reply);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
query_srv_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    struct ares_srv_reply *srv_reply, *srv_ptr;
    PyObject *dns_result, *errorno, *tmp, *result, *callback;

    srv_reply = NULL;
    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_srv_reply(answer_buf, answer_len, &srv_reply);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyList_New(0);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    for (srv_ptr = srv_reply; srv_ptr != NULL; srv_ptr = srv_ptr->next) {
        tmp = PyStructSequence_New(&AresQuerySRVResultType);
        if (tmp == NULL) {
            break;
        }
        PyStructSequence_SET_ITEM(tmp, 0, Py_BuildValue("s", srv_ptr->host));
        PyStructSequence_SET_ITEM(tmp, 1, PyInt_FromLong((long)srv_ptr->port));
        PyStructSequence_SET_ITEM(tmp, 2, PyInt_FromLong((long)srv_ptr->priority));
        PyStructSequence_SET_ITEM(tmp, 3, PyInt_FromLong((long)srv_ptr->weight));
        PyStructSequence_SET_ITEM(tmp, 4, PyInt_FromLong((long)srv_ptr->ttl));
        PyList_Append(dns_result, tmp);
        Py_DECREF(tmp);
    }
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (srv_reply) {
        ares_free_data(srv_reply);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
query_naptr_cb(void *arg, int status,int timeouts, unsigned char *answer_buf, int answer_len)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    int parse_status;
    struct ares_naptr_reply *naptr_reply, *naptr_ptr;
    PyObject *dns_result, *errorno, *tmp, *result, *callback;

    naptr_reply = NULL;
    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    parse_status = ares_parse_naptr_reply(answer_buf, answer_len, &naptr_reply);
    if (parse_status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)parse_status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyList_New(0);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    for (naptr_ptr = naptr_reply; naptr_ptr != NULL; naptr_ptr = naptr_ptr->next) {
        tmp = PyStructSequence_New(&AresQueryNAPTRResultType);
        if (tmp == NULL) {
            break;
        }
        PyStructSequence_SET_ITEM(tmp, 0, PyInt_FromLong((long)naptr_ptr->order));
        PyStructSequence_SET_ITEM(tmp, 1, PyInt_FromLong((long)naptr_ptr->preference));
        PyStructSequence_SET_ITEM(tmp, 2, Py_BuildValue("s", (char *)naptr_ptr->flags));
        PyStructSequence_SET_ITEM(tmp, 3, Py_BuildValue("s", (char *)naptr_ptr->service));
        PyStructSequence_SET_ITEM(tmp, 4, Py_BuildValue("s", (char *)naptr_ptr->regexp));
        PyStructSequence_SET_ITEM(tmp, 5, Py_BuildValue("s", naptr_ptr->replacement));
        PyStructSequence_SET_ITEM(tmp, 6, PyInt_FromLong((long)naptr_ptr->ttl));
        PyList_Append(dns_result, tmp);
        Py_DECREF(tmp);
    }
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);
    if (naptr_reply) {
        ares_free_data(naptr_reply);
    }
    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
host_cb(void *arg, int status, int timeouts, struct hostent *hostent)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    char ip[INET6_ADDRSTRLEN];
    char **ptr;
    PyObject *callback, *dns_name, *errorno, *dns_aliases, *dns_addrlist, *dns_result, *tmp, *result;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_aliases = PyList_New(0);
    dns_addrlist = PyList_New(0);
    dns_result = PyStructSequence_New(&AresHostResultType);

    if (!(dns_aliases && dns_addrlist && dns_result)) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        Py_XDECREF(dns_aliases);
        Py_XDECREF(dns_addrlist);
        Py_XDECREF(dns_result);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    for (ptr = hostent->h_aliases; *ptr != NULL; ptr++) {
        if (*ptr != hostent->h_name && strcmp(*ptr, hostent->h_name)) {
            tmp = Py_BuildValue("s", *ptr);
            if (tmp == NULL) {
                break;
            }
            PyList_Append(dns_aliases, tmp);
            Py_DECREF(tmp);
        }
    }
    for (ptr = hostent->h_addr_list; *ptr != NULL; ptr++) {
        if (hostent->h_addrtype == AF_INET) {
            ares_inet_ntop(AF_INET, *ptr, ip, INET_ADDRSTRLEN);
            tmp = Py_BuildValue("s", ip);
        } else if (hostent->h_addrtype == AF_INET6) {
            ares_inet_ntop(AF_INET6, *ptr, ip, INET6_ADDRSTRLEN);
            tmp = Py_BuildValue("s", ip);
        } else {
            continue;
        }
        if (tmp == NULL) {
            break;
        }
        PyList_Append(dns_addrlist, tmp);
        Py_DECREF(tmp);
    }
    dns_name = Py_BuildValue("s", hostent->h_name);

    PyStructSequence_SET_ITEM(dns_result, 0, dns_name);
    PyStructSequence_SET_ITEM(dns_result, 1, dns_aliases);
    PyStructSequence_SET_ITEM(dns_result, 2, dns_addrlist);
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);

    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static void
nameinfo_cb(void *arg, int status, int timeouts, char *node, char *service)
{
    PyGILState_STATE gstate = PyGILState_Ensure();
    PyObject *callback, *errorno, *dns_node, *dns_service, *dns_result, *result;

    callback = (PyObject *)arg;
    ASSERT(callback);

    if (status != ARES_SUCCESS) {
        errorno = PyInt_FromLong((long)status);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_result = PyStructSequence_New(&AresNameinfoResultType);
    if (!dns_result) {
        PyErr_NoMemory();
        PyErr_WriteUnraisable(Py_None);
        errorno = PyInt_FromLong((long)ARES_ENOMEM);
        dns_result = Py_None;
        Py_INCREF(Py_None);
        goto callback;
    }

    dns_node = Py_BuildValue("s", node);
    if (service) {
        dns_service = Py_BuildValue("s", service);
    } else {
        dns_service = Py_None;
        Py_INCREF(Py_None);
    }

    PyStructSequence_SET_ITEM(dns_result, 0, dns_node);
    PyStructSequence_SET_ITEM(dns_result, 1, dns_service);
    errorno = Py_None;
    Py_INCREF(Py_None);

callback:
    result = PyObject_CallFunctionObjArgs(callback, dns_result, errorno, NULL);
    if (result == NULL) {
        PyErr_WriteUnraisable(callback);
    }
    Py_XDECREF(result);
    Py_DECREF(dns_result);
    Py_DECREF(errorno);

    Py_DECREF(callback);
    PyGILState_Release(gstate);
}


static PyObject *
Channel_func_query(Channel *self, PyObject *args)
{
    char *name;
    int query_type;
    PyObject *callback, *ret;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "etiO:query", "idna", &name, &query_type, &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "a callable is required");
        ret = NULL;
        goto finally;
    }

    Py_INCREF(callback);

    switch (query_type) {
        case T_A:
        {
            ares_query(self->channel, name, C_IN, T_A, &query_a_cb, (void *)callback);
            break;
        }

        case T_AAAA:
        {
            ares_query(self->channel, name, C_IN, T_AAAA, &query_aaaa_cb, (void *)callback);
            break;
        }

        case T_CNAME:
        {
            ares_query(self->channel, name, C_IN, T_CNAME, &query_cname_cb, (void *)callback);
            break;
        }

        case T_MX:
        {
            ares_query(self->channel, name, C_IN, T_MX, &query_mx_cb, (void *)callback);
            break;
        }

        case T_NAPTR:
        {
            ares_query(self->channel, name, C_IN, T_NAPTR, &query_naptr_cb, (void *)callback);
            break;
        }

        case T_NS:
        {
            ares_query(self->channel, name, C_IN, T_NS, &query_ns_cb, (void *)callback);
            break;
        }

        case T_PTR:
        {
            ares_query(self->channel, name, C_IN, T_PTR, &query_ptr_cb, (void *)callback);
            break;
        }

        case T_SOA:
        {
            ares_query(self->channel, name, C_IN, T_SOA, &query_soa_cb, (void *)callback);
            break;
        }

        case T_SRV:
        {
            ares_query(self->channel, name, C_IN, T_SRV, &query_srv_cb, (void *)callback);
            break;
        }

        case T_TXT:
        {
            ares_query(self->channel, name, C_IN, T_TXT, &query_txt_cb, (void *)callback);
            break;
        }

        default:
        {
            Py_DECREF(callback);
            PyErr_SetString(PyExc_ValueError, "invalid query type specified");
            ret = NULL;
            goto finally;
        }
    }
    ret = Py_None;

finally:
    PyMem_Free(name);
    Py_XINCREF(ret);
    return ret;
}


static PyObject *
Channel_func_gethostbyname(Channel *self, PyObject *args)
{
    char *name;
    int family;
    PyObject *callback, *ret;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "etiO:gethostbyname", "idna", &name, &family, &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "a callable is required");
        ret = NULL;
        goto finally;
    }

    Py_INCREF(callback);
    ares_gethostbyname(self->channel, name, family, &host_cb, (void *)callback);
    ret = Py_None;

finally:
    PyMem_Free(name);
    Py_XINCREF(ret);
    return ret;
}


static PyObject *
Channel_func_gethostbyaddr(Channel *self, PyObject *args)
{
    char *name;
    int family, length;
    void *address;
    struct in_addr addr4;
    struct in6_addr addr6;
    PyObject *callback;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "sO:gethostbyaddr", &name, &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "a callable is required");
        return NULL;
    }

    if (ares_inet_pton(AF_INET, name, &addr4) == 1) {
        length = sizeof(struct in_addr);
        address = (void *)&addr4;
        family = AF_INET;
    } else if (ares_inet_pton(AF_INET6, name, &addr6) == 1) {
        length = sizeof(struct in6_addr);
        address = (void *)&addr6;
        family = AF_INET6;
    } else {
        PyErr_SetString(PyExc_ValueError, "invalid IP address");
        return NULL;
    }

    Py_INCREF(callback);
    ares_gethostbyaddr(self->channel, address, length, family, &host_cb, (void *)callback);

    Py_RETURN_NONE;
}


static PyObject *
Channel_func_getnameinfo(Channel *self, PyObject *args)
{
    char *addr;
    int port, flags, length;
    struct in_addr addr4;
    struct in6_addr addr6;
    struct sockaddr *sa;
    struct sockaddr_in sa4;
    struct sockaddr_in6 sa6;
    PyObject *callback;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "(si)iO:getnameinfo", &addr, &port, &flags, &callback)) {
        return NULL;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "a callable is required");
        return NULL;
    }

    if (port < 0 || port > 65535) {
        PyErr_SetString(PyExc_ValueError, "port must be between 0 and 65535");
        return NULL;
    }

    if (ares_inet_pton(AF_INET, addr, &addr4) == 1) {
        sa4 = uv_ip4_addr(addr, port);
        sa = (struct sockaddr *)&sa4;
        length = sizeof(struct sockaddr_in);
    } else if (ares_inet_pton(AF_INET6, addr, &addr6) == 1) {
        sa6 = uv_ip6_addr(addr, port);
        sa = (struct sockaddr *)&sa6;
        length = sizeof(struct sockaddr_in6);
    } else {
        PyErr_SetString(PyExc_ValueError, "invalid IP address");
        return NULL;
    }

    Py_INCREF(callback);
    ares_getnameinfo(self->channel, sa, length, flags, &nameinfo_cb, (void *)callback);

    Py_RETURN_NONE;
}


static PyObject *
Channel_func_cancel(Channel *self)
{
    CHECK_CHANNEL(self);
    ares_cancel(self->channel);
    Py_RETURN_NONE;
}


static PyObject *
Channel_func_destroy(Channel *self)
{
    CHECK_CHANNEL(self);
    ares_destroy(self->channel);
    self->channel = NULL;
    Py_RETURN_NONE;
}


static PyObject *
Channel_func_set_local_ip(Channel *self, PyObject *args)
{
    char *ip;
    struct in_addr addr4;
    struct in6_addr addr6;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "s:set_local_ip", &ip)) {
        return NULL;
    }

    if (ares_inet_pton(AF_INET, ip, &addr4) == 1) {
        ares_set_local_ip4(self->channel, ntohl(addr4.s_addr));
    } else if (ares_inet_pton(AF_INET6, ip, &addr6) == 1) {
        ares_set_local_ip6(self->channel, addr6.s6_addr);
    } else {
        PyErr_SetString(PyExc_ValueError, "invalid IP address");
        return NULL;
    }

    Py_RETURN_NONE;
}


static PyObject *
Channel_func_set_local_dev(Channel *self, PyObject *args)
{
    char *dev;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "s:set_local_dev", &dev)) {
        return NULL;
    }
    ares_set_local_dev(self->channel, dev);

    Py_RETURN_NONE;
}


static PyObject *
Channel_func_process_fd(Channel *self, PyObject *args)
{
    long read_fd, write_fd;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "ll:process_fd", &read_fd, &write_fd)) {
        return NULL;
    }

    ares_process_fd(self->channel, (ares_socket_t)read_fd, (ares_socket_t)write_fd);
    Py_RETURN_NONE;
}


/* borrowed from signalmodule.c */
static inline void
timeval_from_double(double d, struct timeval *tv)
{
    tv->tv_sec = (long)floor(d);
    tv->tv_usec = (long)(fmod(d, 1.0) * 1000000.0);
}

static inline double
double_from_timeval(struct timeval *tv)
{
    return (double)tv->tv_sec + (double)(tv->tv_usec / 1000000.0);
}

static PyObject *
Channel_func_timeout(Channel *self, PyObject *args)
{
    double timeout = -1;
    struct timeval tv, maxtv, *tvp, *maxtvp;

    CHECK_CHANNEL(self);

    if (!PyArg_ParseTuple(args, "|d:timeout", &timeout)) {
        return NULL;
    }

    if (timeout != -1 && timeout < 0.0) {
        PyErr_SetString(PyExc_ValueError, "timeout needs to be a positive number");
        return NULL;
    }

    if (timeout != -1) {
        timeval_from_double(timeout, &maxtv);
        maxtvp = &maxtv;
    } else {
        maxtvp = NULL;
    }

    tvp = ares_timeout(self->channel, maxtvp, &tv);
    if (tvp == NULL)
        return PyFloat_FromDouble(0.0);
    else
        return PyFloat_FromDouble(double_from_timeval(tvp));
}


static PyObject *
Channel_func_getsock(Channel *self)
{
    int i, bitmask;
    ares_socket_t socks[ARES_GETSOCK_MAXNUM];
    PyObject *tpl, *rfds, *wfds, *item;

    CHECK_CHANNEL(self);

    tpl = PyTuple_New(2);
    rfds = PyList_New(0);
    wfds = PyList_New(0);
    if (!tpl || !rfds || !wfds) {
        PyErr_NoMemory();
        Py_XDECREF(tpl);
        Py_XDECREF(rfds);
        Py_XDECREF(wfds);
        return NULL;
    }

    bitmask = ares_getsock(self->channel, socks, ARES_GETSOCK_MAXNUM);
    for(i=0; i < ARES_GETSOCK_MAXNUM; i++) {
        if(ARES_GETSOCK_READABLE(bitmask, i)) {
            item = PyInt_FromLong((long)socks[i]);
            PyList_Append(rfds, item);
            Py_DECREF(item);
        }
        if(ARES_GETSOCK_WRITABLE(bitmask, i)) {
            item = PyInt_FromLong((long)socks[i]);
            PyList_Append(wfds, item);
            Py_DECREF(item);
        }
    }

    PyTuple_SET_ITEM(tpl, 0, rfds);
    PyTuple_SET_ITEM(tpl, 1, wfds);
    return tpl;
}


static int
set_nameservers(Channel *self, PyObject *value)
{
    char *server;
    int i, r, length, ret;
    struct ares_addr_node *servers;
    Py_buffer pbuf;
    PyObject *server_list, *item, *data_fast;

    servers = NULL;
    server_list = value;
    ret = 0;

    if ((data_fast = PySequence_Fast(server_list, "argument 1 must be an iterable")) == NULL) {
        return -1;
    }

    length = PySequence_Fast_GET_SIZE(data_fast);
    if (length > INT_MAX) {
        PyErr_SetString(PyExc_ValueError, "argument 1 is too long");
        Py_DECREF(data_fast);
        return -1;
    }

    if (length == 0) {
        /* c-ares doesn't do anything */
        return 0;
    }

    servers = PyMem_Malloc(sizeof(struct ares_addr_node) * length);
    if (!servers) {
        PyErr_NoMemory();
        ret = -1;
        goto end;
    }

    for (i = 0; i < length; i++) {
        item = PySequence_Fast_GET_ITEM(data_fast, i);
        if (!item || !PyArg_Parse(item, "s*;args contains a non-string value", &pbuf)) {
            goto end;
        }
        server = pbuf.buf;

        if (ares_inet_pton(AF_INET, server, &servers[i].addr.addr4) == 1) {
            servers[i].family = AF_INET;
        } else if (ares_inet_pton(AF_INET6, server, &servers[i].addr.addr6) == 1) {
            servers[i].family = AF_INET6;
        } else {
            PyErr_SetString(PyExc_ValueError, "invalid IP address");
            PyBuffer_Release(&pbuf);
            ret = -1;
            goto end;
        }

        PyBuffer_Release(&pbuf);

        if (i > 0) {
            servers[i-1].next = &servers[i];
        }

    }

    if (servers) {
        servers[length-1].next = NULL;
    }

    r = ares_set_servers(self->channel, servers);
    if (r != ARES_SUCCESS) {
        RAISE_ARES_EXCEPTION(r);
        ret = -1;
    }

end:
    PyMem_Free(servers);
    return ret;
}


static PyObject *
Channel_servers_get(Channel *self, void *closure)
{
    int r;
    char ip[INET6_ADDRSTRLEN];
    struct ares_addr_node *server, *servers;
    PyObject *server_list;
    PyObject *tmp;

    UNUSED_ARG(closure);

    if (!self->channel) {
        PyErr_SetString(PyExc_AresError, "Channel has already been destroyed");
        return NULL;
    }

    server_list = PyList_New(0);
    if (!server_list) {
        PyErr_NoMemory();
        return NULL;
    }

    r = ares_get_servers(self->channel, &servers);
    if (r != ARES_SUCCESS) {
        RAISE_ARES_EXCEPTION(r);
        return NULL;
    }

    for (server = servers; server != NULL; server = server->next) {
        if (server->family == AF_INET) {
            ares_inet_ntop(AF_INET, &(server->addr.addr4), ip, INET_ADDRSTRLEN);
            tmp = Py_BuildValue("s", ip);
        } else {
            ares_inet_ntop(AF_INET6, &(server->addr.addr6), ip, INET6_ADDRSTRLEN);
            tmp = Py_BuildValue("s", ip);
        }
        if (tmp == NULL) {
            break;
        }
        r = PyList_Append(server_list, tmp);
        Py_DECREF(tmp);
        if (r != 0) {
            break;
        }
    }

    return server_list;
}


static int
Channel_servers_set(Channel *self, PyObject *value, void *closure)
{
    UNUSED_ARG(closure);
    if (!self->channel) {
        PyErr_SetString(PyExc_AresError, "Channel has already been destroyed");
        return -1;
    }
    return set_nameservers(self, value);
}


static void free_domains(char **domains)
{
    char **ptr;

    if (domains) {
        for (ptr = domains; *ptr; ptr++) {
            PyMem_Free(*ptr);
        }
        PyMem_Free(domains);
    }
}


static void process_domains(PyObject *domains, char ***rdomains, int *ndomains)
{
    Py_ssize_t i, n;
    PyObject *item, *data_fast;
    char **c_domains;
    char *arg_str, *tmp_str;

    c_domains = NULL;

    *rdomains = NULL;
    *ndomains = 0;

    if ((data_fast = PySequence_Fast(domains, "argument 1 must be an iterable")) == NULL) {
        goto cleanup;
    }

    n = PySequence_Fast_GET_SIZE(data_fast);
    if (n > INT_MAX) {
        PyErr_SetString(PyExc_ValueError, "argument 1 is too long");
        goto cleanup;
    }

    if (n == 0) {
        return;
    }

    c_domains = (char **)PyMem_Malloc(sizeof(char *) * n+1);
    if (!c_domains) {
        PyErr_NoMemory();
        goto cleanup;
    }
    memset(c_domains, 0, n+1);
    i = 0;
    while (i < n) {
        item = PySequence_Fast_GET_ITEM(data_fast, i);
        if (!item || !PyArg_Parse(item, "s;args contains a non-string value", &arg_str)) {
            Py_XDECREF(item);
            goto cleanup;
        }
        Py_DECREF(item);
        tmp_str = (char *) PyMem_Malloc(strlen(arg_str) + 1);
        if (!tmp_str) {
            PyErr_NoMemory();
            goto cleanup;
        }
        strcpy(tmp_str, arg_str);
        c_domains[i] = tmp_str;
        i++;
    }
    c_domains[n] = NULL;

    *rdomains = c_domains;
    *ndomains = n;
    return;

cleanup:
    *rdomains = NULL;
    *ndomains = -1;
    free_domains(c_domains);
}


static int
Channel_tp_init(Channel *self, PyObject *args, PyObject *kwargs)
{
    int r, flags, tries, ndots, tcp_port, udp_port, optmask, ndomains, socket_send_buffer_size, socket_receive_buffer_size;
    char *lookups;
    char **c_domains;
    double timeout;
    struct ares_options options;
    PyObject *servers, *domains, *sock_state_cb, *rotate;

    static char *kwlist[] = {"flags", "timeout", "tries", "ndots", "tcp_port", "udp_port",
                             "servers", "domains", "lookups", "sock_state_cb",
                             "socket_send_buffer_size", "socket_receive_buffer_size", "rotate", NULL};

    optmask = 0;
    flags = tries = ndots = tcp_port = udp_port = socket_send_buffer_size = socket_receive_buffer_size = -1;
    timeout = -1.0;
    lookups = NULL;
    c_domains = NULL;
    servers = domains = sock_state_cb = NULL;
    rotate = Py_False;

    if (self->channel) {
        PyErr_SetString(PyExc_AresError, "Object already initialized");
        return -1;
    }

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|idiiiiOOsOiiO!:__init__", kwlist, &flags, &timeout, &tries, &ndots, &tcp_port, &udp_port, &servers,
                                                                                       &domains, &lookups, &sock_state_cb, &socket_send_buffer_size, &socket_receive_buffer_size,
                                                                                       &PyBool_Type, &rotate)) {
        return -1;
    }

    if (sock_state_cb && !PyCallable_Check(sock_state_cb)) {
        PyErr_SetString(PyExc_TypeError, "sock_state_cb is not callable");
        return -1;
    }

    r = ares_library_init(ARES_LIB_INIT_ALL);
    if (r != ARES_SUCCESS) {
        RAISE_ARES_EXCEPTION(r);
        return -1;
    }
    self->lib_initialized = True;

    memset(&options, 0, sizeof(struct ares_options));

    if (flags != -1) {
        options.flags = flags;
        optmask |= ARES_OPT_FLAGS;
    }
    if (timeout != -1) {
        options.timeout = (int)(timeout * 1000);
        optmask |= ARES_OPT_TIMEOUTMS;
    }
    if (tries != -1) {
        options.tries = tries;
        optmask |= ARES_OPT_TRIES;
    }
    if (ndots != -1) {
        options.ndots = ndots;
        optmask |= ARES_OPT_NDOTS;
    }
    if (tcp_port != -1) {
        options.tcp_port = tcp_port;
        optmask |= ARES_OPT_TCP_PORT;
    }
    if (udp_port != -1) {
        options.udp_port = udp_port;
        optmask |= ARES_OPT_UDP_PORT;
    }
    if (socket_send_buffer_size != -1) {
        options.socket_send_buffer_size = socket_send_buffer_size;
        optmask |= ARES_OPT_SOCK_SNDBUF;
    }
    if (socket_receive_buffer_size != -1) {
        options.socket_receive_buffer_size = socket_receive_buffer_size;
        optmask |= ARES_OPT_SOCK_RCVBUF;
    }
    if (sock_state_cb) {
        options.sock_state_cb = ares__sock_state_cb;
        options.sock_state_cb_data = (void *)self;
        optmask |= ARES_OPT_SOCK_STATE_CB;
        Py_INCREF(sock_state_cb);
        self->sock_state_cb = sock_state_cb;
    }
    if (lookups) {
        options.lookups = lookups;
        optmask |= ARES_OPT_LOOKUPS;
    }
    if (domains) {
        process_domains(domains, &c_domains, &ndomains);
        if (ndomains == -1) {
            goto error;
        }
        options.domains = c_domains;
        options.ndomains = ndomains;
        optmask |= ARES_OPT_DOMAINS;
    }
    if (rotate == Py_True) {
        optmask |= ARES_OPT_ROTATE;
    }

    r = ares_init_options(&self->channel, &options, optmask);
    if (r != ARES_SUCCESS) {
        RAISE_ARES_EXCEPTION(r);
        goto error;
    }

    free_domains(c_domains);

    if (servers) {
        return set_nameservers(self, servers);
    }

    return 0;

error:
    free_domains(c_domains);
    Py_XDECREF(sock_state_cb);
    return -1;
}



static PyObject *
Channel_tp_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
    Channel *self = (Channel *)PyType_GenericNew(type, args, kwargs);
    if (!self) {
        return NULL;
    }
    self->channel = NULL;
    self->lib_initialized = False;
    return (PyObject *)self;
}


static int
Channel_tp_traverse(Channel *self, visitproc visit, void *arg)
{
    Py_VISIT(self->sock_state_cb);
    return 0;
}


static int
Channel_tp_clear(Channel *self)
{
    Py_CLEAR(self->sock_state_cb);
    return 0;
}


static void
Channel_tp_dealloc(Channel *self)
{
    if (self->channel) {
        ares_destroy(self->channel);
        self->channel = NULL;
    }
    if (self->lib_initialized) {
        ares_library_cleanup();
    }
    Channel_tp_clear(self);
    Py_TYPE(self)->tp_free((PyObject *)self);
}


static PyMethodDef
Channel_tp_methods[] = {
    { "gethostbyname", (PyCFunction)Channel_func_gethostbyname, METH_VARARGS, "Gethostbyname" },
    { "gethostbyaddr", (PyCFunction)Channel_func_gethostbyaddr, METH_VARARGS, "Gethostbyaddr" },
    { "getnameinfo", (PyCFunction)Channel_func_getnameinfo, METH_VARARGS, "Getnameinfo" },
    { "query", (PyCFunction)Channel_func_query, METH_VARARGS, "Run a DNS query of the specified type" },
    { "cancel", (PyCFunction)Channel_func_cancel, METH_NOARGS, "Cancel all pending queries on this resolver" },
    { "destroy", (PyCFunction)Channel_func_destroy, METH_NOARGS, "Destroy this channel, it will no longer be usable" },
    { "process_fd", (PyCFunction)Channel_func_process_fd, METH_VARARGS, "Process file descriptors actions" },
    { "getsock", (PyCFunction)Channel_func_getsock, METH_NOARGS, "Set of file descriptors the application needs to poll" },
    { "set_local_ip", (PyCFunction)Channel_func_set_local_ip, METH_VARARGS, "Set source IP address" },
    { "set_local_dev", (PyCFunction)Channel_func_set_local_dev, METH_VARARGS, "Set source device name" },
    { "timeout", (PyCFunction)Channel_func_timeout, METH_VARARGS, "Determine polling timeout" },
    { NULL }
};


static PyGetSetDef Channel_tp_getsets[] = {
    {"servers", (getter)Channel_servers_get, (setter)Channel_servers_set, "DNS nameservers", NULL},
    {NULL}
};


static PyTypeObject ChannelType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "pycares.Channel",                                              /*tp_name*/
    sizeof(Channel),                                                /*tp_basicsize*/
    0,                                                              /*tp_itemsize*/
    (destructor)Channel_tp_dealloc,                                 /*tp_dealloc*/
    0,                                                              /*tp_print*/
    0,                                                              /*tp_getattr*/
    0,                                                              /*tp_setattr*/
    0,                                                              /*tp_compare*/
    0,                                                              /*tp_repr*/
    0,                                                              /*tp_as_number*/
    0,                                                              /*tp_as_sequence*/
    0,                                                              /*tp_as_mapping*/
    0,                                                              /*tp_hash */
    0,                                                              /*tp_call*/
    0,                                                              /*tp_str*/
    0,                                                              /*tp_getattro*/
    0,                                                              /*tp_setattro*/
    0,                                                              /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,                        /*tp_flags*/
    0,                                                              /*tp_doc*/
    (traverseproc)Channel_tp_traverse,                              /*tp_traverse*/
    (inquiry)Channel_tp_clear,                                      /*tp_clear*/
    0,                                                              /*tp_richcompare*/
    0,                                                              /*tp_weaklistoffset*/
    0,                                                              /*tp_iter*/
    0,                                                              /*tp_iternext*/
    Channel_tp_methods,                                             /*tp_methods*/
    0,                                                              /*tp_members*/
    Channel_tp_getsets,                                             /*tp_getsets*/
    0,                                                              /*tp_base*/
    0,                                                              /*tp_dict*/
    0,                                                              /*tp_descr_get*/
    0,                                                              /*tp_descr_set*/
    0,                                                              /*tp_dictoffset*/
    (initproc)Channel_tp_init,                                      /*tp_init*/
    0,                                                              /*tp_alloc*/
    Channel_tp_new,                                                 /*tp_new*/
};


