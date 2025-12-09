
import cffi
import sys


if sys.platform == 'win32':
    PLATFORM_TYPES = """
typedef long time_t;
typedef long suseconds_t;
typedef short h_addrtype_t;
typedef short h_length_t;
typedef short sa_family_t;
typedef unsigned short in_port_t;
"""
else:
    PLATFORM_TYPES = """
typedef long... time_t;
typedef long... suseconds_t;
typedef int h_addrtype_t;
typedef int h_length_t;
typedef int... sa_family_t;
typedef uint16_t in_port_t;
"""

TYPES = """
struct in_addr {
    uint32_t s_addr;
};

struct in6_addr {
    uint8_t s6_addr[16];
    ...;
};

struct timeval {
    time_t      tv_sec;
    suseconds_t tv_usec;
};

struct hostent {
   char         *h_name;
   char         **h_aliases;
   h_addrtype_t h_addrtype;
   h_length_t   h_length;
   char         **h_addr_list;
};

struct sockaddr {
    sa_family_t sa_family;
    ...;
};

struct sockaddr_in {
    sa_family_t       sin_family;
    in_port_t         sin_port;
    struct in_addr    sin_addr;
    ...;
};

struct sockaddr_in6 {
    sa_family_t         sin6_family;
    in_port_t           sin6_port;
    uint32_t            sin6_flowinfo;
    struct in6_addr     sin6_addr;
    uint32_t            sin6_scope_id;
    ...;
};

#define INET_ADDRSTRLEN ...
#define INET6_ADDRSTRLEN ...

/* DNS record types */
typedef enum {
  ARES_REC_TYPE_A = 1,
  ARES_REC_TYPE_NS = 2,
  ARES_REC_TYPE_CNAME = 5,
  ARES_REC_TYPE_SOA = 6,
  ARES_REC_TYPE_PTR = 12,
  ARES_REC_TYPE_MX = 15,
  ARES_REC_TYPE_TXT = 16,
  ARES_REC_TYPE_AAAA = 28,
  ARES_REC_TYPE_SRV = 33,
  ARES_REC_TYPE_NAPTR = 35,
  ARES_REC_TYPE_TLSA = 52,
  ARES_REC_TYPE_HTTPS = 65,
  ARES_REC_TYPE_CAA = 257,
  ARES_REC_TYPE_URI = 256,
  ARES_REC_TYPE_ANY = 255,
  ...
} ares_dns_rec_type_t;

/* DNS classes */
typedef enum {
  ARES_CLASS_IN = 1,
  ARES_CLASS_CHAOS = 3,
  ARES_CLASS_HESOID = 4,
  ARES_CLASS_NONE = 254,
  ARES_CLASS_ANY = 255,
  ...
} ares_dns_class_t;

/* DNS sections */
typedef enum {
  ARES_SECTION_ANSWER = 1,
  ARES_SECTION_AUTHORITY = 2,
  ARES_SECTION_ADDITIONAL = 3,
  ...
} ares_dns_section_t;

/* DNS Header opcodes */
typedef enum {
  ARES_OPCODE_QUERY = 0,
  ARES_OPCODE_IQUERY = 1,
  ARES_OPCODE_STATUS = 2,
  ARES_OPCODE_NOTIFY = 4,
  ARES_OPCODE_UPDATE = 5,
  ...
} ares_dns_opcode_t;

/* DNS Response codes */
typedef enum {
  ARES_RCODE_NOERROR = 0,
  ARES_RCODE_FORMERR = 1,
  ARES_RCODE_SERVFAIL = 2,
  ARES_RCODE_NXDOMAIN = 3,
  ARES_RCODE_NOTIMP = 4,
  ARES_RCODE_REFUSED = 5,
  ARES_RCODE_YXDOMAIN = 6,
  ARES_RCODE_YXRRSET = 7,
  ARES_RCODE_NXRRSET = 8,
  ARES_RCODE_NOTAUTH = 9,
  ARES_RCODE_NOTZONE = 10,
  ARES_RCODE_DSOTYPEI = 11,
  ARES_RCODE_BADSIG = 16,
  ARES_RCODE_BADKEY = 17,
  ARES_RCODE_BADTIME = 18,
  ARES_RCODE_BADMODE = 19,
  ARES_RCODE_BADNAME = 20,
  ARES_RCODE_BADALG = 21,
  ARES_RCODE_BADTRUNC = 22,
  ARES_RCODE_BADCOOKIE = 23,
  ...
} ares_dns_rcode_t;

/* DNS Header flags */
typedef enum {
  ARES_FLAG_QR = 1 << 0,
  ARES_FLAG_AA = 1 << 1,
  ARES_FLAG_TC = 1 << 2,
  ARES_FLAG_RD = 1 << 3,
  ARES_FLAG_RA = 1 << 4,
  ARES_FLAG_AD = 1 << 5,
  ARES_FLAG_CD = 1 << 6,
  ...
} ares_dns_flags_t;

/* DNS RR keys for accessing record fields */
typedef enum {
  /* A record */
  ARES_RR_A_ADDR = 1,

  /* AAAA record */
  ARES_RR_AAAA_ADDR = 1,

  /* NS record */
  ARES_RR_NS_NSDNAME = 1,

  /* CNAME record */
  ARES_RR_CNAME_CNAME = 1,

  /* SOA record */
  ARES_RR_SOA_MNAME = 1,
  ARES_RR_SOA_RNAME = 2,
  ARES_RR_SOA_SERIAL = 3,
  ARES_RR_SOA_REFRESH = 4,
  ARES_RR_SOA_RETRY = 5,
  ARES_RR_SOA_EXPIRE = 6,
  ARES_RR_SOA_MINIMUM = 7,

  /* PTR record */
  ARES_RR_PTR_DNAME = 1,

  /* MX record */
  ARES_RR_MX_PREFERENCE = 1,
  ARES_RR_MX_EXCHANGE = 2,

  /* TXT record */
  ARES_RR_TXT_DATA = 1,

  /* SRV record */
  ARES_RR_SRV_PRIORITY = 1,
  ARES_RR_SRV_WEIGHT = 2,
  ARES_RR_SRV_PORT = 3,
  ARES_RR_SRV_TARGET = 4,

  /* NAPTR record */
  ARES_RR_NAPTR_ORDER = 1,
  ARES_RR_NAPTR_PREFERENCE = 2,
  ARES_RR_NAPTR_FLAGS = 3,
  ARES_RR_NAPTR_SERVICES = 4,
  ARES_RR_NAPTR_REGEXP = 5,
  ARES_RR_NAPTR_REPLACEMENT = 6,

  /* CAA record */
  ARES_RR_CAA_CRITICAL = 1,
  ARES_RR_CAA_TAG = 2,
  ARES_RR_CAA_VALUE = 3,

  /* TLSA record */
  ARES_RR_TLSA_CERT_USAGE = 5201,
  ARES_RR_TLSA_SELECTOR = 5202,
  ARES_RR_TLSA_MATCH = 5203,
  ARES_RR_TLSA_DATA = 5204,

  /* HTTPS record */
  ARES_RR_HTTPS_PRIORITY = 6501,
  ARES_RR_HTTPS_TARGET = 6502,
  ARES_RR_HTTPS_PARAMS = 6503,

  /* URI record */
  ARES_RR_URI_PRIORITY = 25601,
  ARES_RR_URI_WEIGHT = 25602,
  ARES_RR_URI_TARGET = 25603,
  ...
} ares_dns_rr_key_t;

/* Opaque DNS record structures */
typedef struct ares_dns_record ares_dns_record_t;
typedef struct ares_dns_rr ares_dns_rr_t;

typedef int... ares_socket_t;
typedef int... ares_socklen_t;

#define ARES_FLAG_USEVC         ...
#define ARES_FLAG_PRIMARY       ...
#define ARES_FLAG_IGNTC         ...
#define ARES_FLAG_NORECURSE     ...
#define ARES_FLAG_STAYOPEN      ...
#define ARES_FLAG_NOSEARCH      ...
#define ARES_FLAG_NOALIASES     ...
#define ARES_FLAG_NOCHECKRESP   ...
#define ARES_FLAG_EDNS          ...
#define ARES_FLAG_NO_DFLT_SVR   ...

#define ARES_OPT_FLAGS          ...
#define ARES_OPT_TIMEOUT        ...
#define ARES_OPT_TRIES          ...
#define ARES_OPT_NDOTS          ...
#define ARES_OPT_UDP_PORT       ...
#define ARES_OPT_TCP_PORT       ...
#define ARES_OPT_SERVERS        ...
#define ARES_OPT_DOMAINS        ...
#define ARES_OPT_LOOKUPS        ...
#define ARES_OPT_SOCK_STATE_CB  ...
#define ARES_OPT_SORTLIST       ...
#define ARES_OPT_SOCK_SNDBUF    ...
#define ARES_OPT_SOCK_RCVBUF    ...
#define ARES_OPT_TIMEOUTMS      ...
#define ARES_OPT_ROTATE         ...
#define ARES_OPT_EDNSPSZ        ...
#define ARES_OPT_RESOLVCONF     ...
#define ARES_OPT_EVENT_THREAD   ...

#define ARES_NI_NOFQDN                  ...
#define ARES_NI_NUMERICHOST             ...
#define ARES_NI_NAMEREQD                ...
#define ARES_NI_NUMERICSERV             ...
#define ARES_NI_DGRAM                   ...
#define ARES_NI_TCP                     ...
#define ARES_NI_UDP                     ...
#define ARES_NI_SCTP                    ...
#define ARES_NI_DCCP                    ...
#define ARES_NI_NUMERICSCOPE            ...
#define ARES_NI_LOOKUPHOST              ...
#define ARES_NI_LOOKUPSERVICE           ...
#define ARES_NI_IDN                     ...
#define ARES_NI_IDN_ALLOW_UNASSIGNED    ...
#define ARES_NI_IDN_USE_STD3_ASCII_RULES ...

#define ARES_AI_CANONNAME               ...
#define ARES_AI_NUMERICHOST             ...
#define ARES_AI_PASSIVE                 ...
#define ARES_AI_NUMERICSERV             ...
#define ARES_AI_V4MAPPED                ...
#define ARES_AI_ALL                     ...
#define ARES_AI_ADDRCONFIG              ...
#define ARES_AI_IDN                     ...
#define ARES_AI_IDN_ALLOW_UNASSIGNED    ...
#define ARES_AI_IDN_USE_STD3_ASCII_RULES ...
#define ARES_AI_CANONIDN                ...
#define ARES_AI_MASK ...

#define ARES_LIB_INIT_ALL    ...

#define ARES_SOCKET_BAD ...

typedef enum {
  ARES_FALSE = 0,
  ARES_TRUE  = 1
} ares_bool_t;

typedef enum {
  ARES_SUCCESS = 0,

  /* Server error codes (ARES_ENODATA indicates no relevant answer) */
  ARES_ENODATA   = 1,
  ARES_EFORMERR  = 2,
  ARES_ESERVFAIL = 3,
  ARES_ENOTFOUND = 4,
  ARES_ENOTIMP   = 5,
  ARES_EREFUSED  = 6,

  /* Locally generated error codes */
  ARES_EBADQUERY    = 7,
  ARES_EBADNAME     = 8,
  ARES_EBADFAMILY   = 9,
  ARES_EBADRESP     = 10,
  ARES_ECONNREFUSED = 11,
  ARES_ETIMEOUT     = 12,
  ARES_EOF          = 13,
  ARES_EFILE        = 14,
  ARES_ENOMEM       = 15,
  ARES_EDESTRUCTION = 16,
  ARES_EBADSTR      = 17,

  /* ares_getnameinfo error codes */
  ARES_EBADFLAGS = 18,

  /* ares_getaddrinfo error codes */
  ARES_ENONAME   = 19,
  ARES_EBADHINTS = 20,

  /* Uninitialized library error code */
  ARES_ENOTINITIALIZED = 21, /* introduced in 1.7.0 */

  /* ares_library_init error codes */
  ARES_ELOADIPHLPAPI         = 22, /* introduced in 1.7.0 */
  ARES_EADDRGETNETWORKPARAMS = 23, /* introduced in 1.7.0 */

  /* More error codes */
  ARES_ECANCELLED = 24, /* introduced in 1.7.0 */

  /* More ares_getaddrinfo error codes */
  ARES_ESERVICE = 25, /* ares_getaddrinfo() was passed a text service name that
                       * is not recognized. introduced in 1.16.0 */

  ARES_ENOSERVER = 26 /* No DNS servers were configured */
} ares_status_t;

typedef void (*ares_sock_state_cb)(void *data,
                                   ares_socket_t socket_fd,
                                   int readable,
                                   int writable);

typedef void (*ares_callback_dnsrec)(void *arg,
                                     ares_status_t status,
                                     size_t timeouts,
                                     const ares_dns_record_t *dnsrec);

typedef void (*ares_host_callback)(void *arg,
                                   int status,
                                   int timeouts,
                                   struct hostent *hostent);

typedef void (*ares_nameinfo_callback)(void *arg,
                                       int status,
                                       int timeouts,
                                       char *node,
                                       char *service);

typedef int  (*ares_sock_create_callback)(ares_socket_t socket_fd,
                                          int type,
                                          void *data);

typedef void (*ares_addrinfo_callback)(void *arg,
                                   int status,
                                   int timeouts,
                                   struct ares_addrinfo *res);

struct ares_channeldata;
typedef struct ares_channeldata *ares_channel;

struct ares_server_failover_options {
  unsigned short retry_chance;
  size_t         retry_delay;
};

/*! Values for ARES_OPT_EVENT_THREAD */
typedef enum {
  /*! Default (best choice) event system */
  ARES_EVSYS_DEFAULT = 0,
  /*! Win32 IOCP/AFD_POLL event system */
  ARES_EVSYS_WIN32 = 1,
  /*! Linux epoll */
  ARES_EVSYS_EPOLL = 2,
  /*! BSD/MacOS kqueue */
  ARES_EVSYS_KQUEUE = 3,
  /*! POSIX poll() */
  ARES_EVSYS_POLL = 4,
  /*! last fallback on Unix-like systems, select() */
  ARES_EVSYS_SELECT = 5
} ares_evsys_t;

struct ares_options {
  int flags;
  int timeout; /* in seconds or milliseconds, depending on options */
  int tries;
  int ndots;
  unsigned short udp_port; /* host byte order */
  unsigned short tcp_port; /* host byte order */
  int socket_send_buffer_size;
  int socket_receive_buffer_size;
  struct in_addr *servers;
  int nservers;
  char **domains;
  int ndomains;
  char *lookups;
  ares_sock_state_cb sock_state_cb;
  void *sock_state_cb_data;
  struct apattern *sortlist;
  int nsort;
  int ednspsz;
  char *resolvconf_path;
  char *hosts_path;
  int udp_max_queries;
  int maxtimeout; /* in milliseconds */
  unsigned int qcache_max_ttl; /* Maximum TTL for query cache, 0=disabled */
  ares_evsys_t evsys;
  struct ares_server_failover_options server_failover_opts;
  ...;
};

struct ares_in6_addr {
  union {
    unsigned char _S6_u8[16];
  } _S6_un;
};

struct ares_addrttl {
  struct in_addr ipaddr;
  int            ttl;
};

struct ares_addr6ttl {
  struct ares_in6_addr ip6addr;
  int             ttl;
};

struct ares_caa_reply {
  struct ares_caa_reply  *next;
  int                     critical;
  unsigned char          *property;
  size_t                  plength;
  unsigned char          *value;
  size_t                  length;
};

struct ares_srv_reply {
  struct ares_srv_reply  *next;
  char                   *host;
  unsigned short          priority;
  unsigned short          weight;
  unsigned short          port;
};

struct ares_mx_reply {
  struct ares_mx_reply   *next;
  char                   *host;
  unsigned short          priority;
};

struct ares_txt_reply {
  struct ares_txt_reply  *next;
  unsigned char          *txt;
  size_t                  length;
};

struct ares_txt_ext {
  struct ares_txt_ext      *next;
  unsigned char            *txt;
  size_t                   length;
  unsigned char            record_start;
};

struct ares_naptr_reply {
  struct ares_naptr_reply *next;
  unsigned char           *flags;
  unsigned char           *service;
  unsigned char           *regexp;
  char                    *replacement;
  unsigned short           order;
  unsigned short           preference;
};

struct ares_soa_reply {
  char        *nsname;
  char        *hostmaster;
  unsigned int serial;
  unsigned int refresh;
  unsigned int retry;
  unsigned int expire;
  unsigned int minttl;
};
/*
 * Similar to addrinfo, but with extra ttl and missing canonname.
 */
struct ares_addrinfo_node {
  int                        ai_ttl;
  int                        ai_flags;
  int                        ai_family;
  int                        ai_socktype;
  int                        ai_protocol;
  ares_socklen_t             ai_addrlen;
  struct sockaddr           *ai_addr;
  struct ares_addrinfo_node *ai_next;
};

/*
 * alias - label of the resource record.
 * name - value (canonical name) of the resource record.
 * See RFC2181 10.1.1. CNAME terminology.
 */
struct ares_addrinfo_cname {
  int                         ttl;
  char                       *alias;
  char                       *name;
  struct ares_addrinfo_cname *next;
};

struct ares_addrinfo {
  struct ares_addrinfo_cname *cnames;
  struct ares_addrinfo_node  *nodes;
  ...;
};

struct ares_addrinfo_hints {
  int ai_flags;
  int ai_family;
  int ai_socktype;
  int ai_protocol;
};
"""

FUNCTIONS = """
int ares_library_init(int flags);

void ares_library_cleanup(void);

const char *ares_version(int *version);

int ares_init_options(ares_channel *channelptr,
                                   struct ares_options *options,
                                   int optmask);

int ares_reinit(ares_channel channel);

int ares_save_options(ares_channel channel,
                                   struct ares_options *options,
                                   int *optmask);

void ares_destroy_options(struct ares_options *options);

int ares_dup(ares_channel *dest,
                          ares_channel src);

void ares_destroy(ares_channel channel);

void ares_cancel(ares_channel channel);

void ares_set_local_ip4(ares_channel channel, unsigned int local_ip);

void ares_set_local_ip6(ares_channel channel,
                                     const unsigned char* local_ip6);

void ares_set_local_dev(ares_channel channel,
                                     const char* local_dev_name);

void ares_set_socket_callback(ares_channel channel,
                                           ares_sock_create_callback callback,
                                           void *user_data);

void ares_getaddrinfo(ares_channel channel,
                                   const char* node,
                                   const char* service,
                                   const struct ares_addrinfo_hints* hints,
                                   ares_addrinfo_callback callback,
                                   void* arg);

void ares_freeaddrinfo(struct ares_addrinfo* ai);

/* New DNS record API */
ares_status_t ares_query_dnsrec(ares_channel channel,
                                const char *name,
                                ares_dns_class_t dnsclass,
                                ares_dns_rec_type_t type,
                                ares_callback_dnsrec callback,
                                void *arg,
                                unsigned short *qid);

ares_status_t ares_search_dnsrec(ares_channel channel,
                                 const ares_dns_record_t *dnsrec,
                                 ares_callback_dnsrec callback,
                                 void *arg);

ares_status_t ares_dns_record_create(ares_dns_record_t **dnsrec,
                                     unsigned short id,
                                     unsigned short flags,
                                     ares_dns_opcode_t opcode,
                                     ares_dns_rcode_t rcode);

ares_status_t ares_dns_record_query_add(ares_dns_record_t *dnsrec,
                                        const char *name,
                                        ares_dns_rec_type_t qtype,
                                        ares_dns_class_t qclass);

void ares_dns_record_destroy(ares_dns_record_t *dnsrec);

size_t ares_dns_record_rr_cnt(const ares_dns_record_t *dnsrec,
                              ares_dns_section_t sect);

const ares_dns_rr_t *ares_dns_record_rr_get_const(const ares_dns_record_t *dnsrec,
                                                  ares_dns_section_t sect,
                                                  size_t idx);

const char *ares_dns_rr_get_name(const ares_dns_rr_t *rr);

ares_dns_rec_type_t ares_dns_rr_get_type(const ares_dns_rr_t *rr);

ares_dns_class_t ares_dns_rr_get_class(const ares_dns_rr_t *rr);

unsigned int ares_dns_rr_get_ttl(const ares_dns_rr_t *rr);

/* Record data accessors */
const struct in_addr *ares_dns_rr_get_addr(const ares_dns_rr_t *rr,
                                           ares_dns_rr_key_t key);

const struct ares_in6_addr *ares_dns_rr_get_addr6(const ares_dns_rr_t *rr,
                                                  ares_dns_rr_key_t key);

const char *ares_dns_rr_get_str(const ares_dns_rr_t *rr,
                               ares_dns_rr_key_t key);

unsigned char ares_dns_rr_get_u8(const ares_dns_rr_t *rr,
                                ares_dns_rr_key_t key);

unsigned short ares_dns_rr_get_u16(const ares_dns_rr_t *rr,
                                  ares_dns_rr_key_t key);

unsigned int ares_dns_rr_get_u32(const ares_dns_rr_t *rr,
                                ares_dns_rr_key_t key);

const unsigned char *ares_dns_rr_get_bin(const ares_dns_rr_t *rr,
                                        ares_dns_rr_key_t key,
                                        size_t *len);

size_t ares_dns_rr_get_abin_cnt(const ares_dns_rr_t *rr,
                               ares_dns_rr_key_t key);

const unsigned char *ares_dns_rr_get_abin(const ares_dns_rr_t *rr,
                                         ares_dns_rr_key_t key,
                                         size_t idx,
                                         size_t *len);

size_t ares_dns_rr_get_opt_cnt(const ares_dns_rr_t *dns_rr,
                               ares_dns_rr_key_t key);

unsigned short ares_dns_rr_get_opt(const ares_dns_rr_t *dns_rr,
                                   ares_dns_rr_key_t key,
                                   size_t idx,
                                   const unsigned char **val,
                                   size_t *val_len);

void ares_gethostbyaddr(ares_channel channel,
                                     const void *addr,
                                     int addrlen,
                                     int family,
                                     ares_host_callback callback,
                                     void *arg);

void ares_getnameinfo(ares_channel channel,
                                   const struct sockaddr *sa,
                                   ares_socklen_t salen,
                                   int flags,
                                   ares_nameinfo_callback callback,
                                   void *arg);

struct timeval *ares_timeout(ares_channel channel,
                                          struct timeval *maxtv,
                                          struct timeval *tv);

void ares_process_fd(ares_channel channel,
                                  ares_socket_t read_fd,
                                  ares_socket_t write_fd);

void ares_free_string(void *str);

void ares_free_hostent(struct hostent *host);

void ares_free_data(void *dataptr);

const char *ares_strerror(int code);

int ares_set_servers_csv(ares_channel channel, const char *servers);

char *ares_get_servers_csv(const ares_channel channel);

const char *ares_inet_ntop(int af, const void *src, char *dst,
                                        ares_socklen_t size);

int ares_inet_pton(int af, const char *src, void *dst);

ares_bool_t ares_threadsafety(void);

ares_status_t ares_queue_wait_empty(ares_channel channel, int timeout_ms);
"""

CALLBACKS = """
extern "Python" void _sock_state_cb(void *data,
                                    ares_socket_t socket_fd,
                                    int readable,
                                    int writable);

extern "Python" void _host_cb(void *arg,
                              int status,
                              int timeouts,
                              struct hostent *hostent);

extern "Python" void _nameinfo_cb(void *arg,
                                  int status,
                                  int timeouts,
                                  char *node,
                                  char *service);

extern "Python" void _query_dnsrec_cb(void *arg,
                                      ares_status_t status,
                                      size_t timeouts,
                                      const ares_dns_record_t *dnsrec);

extern "Python" void _addrinfo_cb(void *arg,
                                  int status,
                                  int timeouts,
                                  struct ares_addrinfo *res);
"""

INCLUDES = """
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
# include <WinSock2.h>
#else
# include <sys/types.h>
# include <sys/socket.h>
# include <netdb.h> /* struct hostent */
# include <netinet/in.h> /* struct sockaddr_in/sockaddr_in6 */
#endif
#include <ares.h>
#include <ares_dns_record.h>
"""


ffi = cffi.FFI()
ffi.cdef(PLATFORM_TYPES + TYPES + FUNCTIONS + CALLBACKS)
ffi.set_source('_cares', INCLUDES)
