
import cffi
import sys
import os
import re


current_dir = os.path.dirname(__file__)
extra_libraries = []

ffi = cffi.FFI()

if sys.platform == 'win32':
    extra_libraries.extend(["ws2_32", "advapi32", "iphlpapi", "psapi"])
    ffi.cdef(re.sub(r"\b(_In_|_Inout_|_Out_|_Outptr_|FAR)(opt_)?\b", " ",
"""
typedef unsigned short...        u_short;
typedef unsigned long...        u_long;

typedef struct fd_set {
    ...;
} fd_set;

struct in_addr {
    uint32_t s_addr;
};

struct in6_addr {
    uint8_t s6_addr[16];
};

typedef struct hostent {
    char FAR      *h_name;
    char FAR  FAR **h_aliases;
    short         h_addrtype;
    short         h_length;
    char FAR  FAR **h_addr_list;
} HOSTENT, *PHOSTENT, FAR *LPHOSTENT;

struct timeval {
    long    tv_sec;         /* seconds */
    long    tv_usec;        /* and microseconds */
};

struct sockaddr {
    short  sa_family;
    ...;
};

struct sockaddr_in {
    short   sin_family;
    u_short sin_port;
    struct  in_addr sin_addr;
    char    sin_zero[8];
};

struct sockaddr_in6 {
    short   sin6_family;
    u_short sin6_port;
    u_long  sin6_flowinfo;
    struct  in6_addr sin6_addr;
    u_long  sin6_scope_id;
};

"""))
else:
    ffi.cdef("""
/* fd_set for select and pselect.  */
typedef struct
{
...;
} fd_set;

struct in_addr {
    uint32_t s_addr;
};

struct in6_addr {
    uint8_t s6_addr[16];
};

typedef long... time_t;
typedef long... suseconds_t;

struct timeval {
    time_t      tv_sec;     /* seconds */
    suseconds_t tv_usec;    /* microseconds */
};

struct hostent {
   char  *h_name;            /* official name of host */
   char **h_aliases;         /* alias list */
   int    h_addrtype;        /* host address type */
   int    h_length;          /* length of address */
   char **h_addr_list;       /* list of addresses */
};

typedef int... sa_family_t;
typedef uint16_t in_port_t;

struct sockaddr {
    sa_family_t sa_family;
    ...;
};

struct sockaddr_in {
    sa_family_t       sin_family; /* Address family       */
    in_port_t         sin_port;   /* Port number          */
    struct in_addr    sin_addr;   /* Internet address     */
    ...;
};

struct sockaddr_in6 {
    sa_family_t         sin6_family;    /* AF_INET6 */
    in_port_t           sin6_port;      /* Transport layer port # */
    uint32_t            sin6_flowinfo;  /* IPv6 flow information */
    struct in6_addr     sin6_addr;      /* IPv6 address */
    uint32_t            sin6_scope_id;  /* scope id (new in RFC2553) */
    ...;
};

""")

ffi.cdef("""

#define INET_ADDRSTRLEN ...
#define INET6_ADDRSTRLEN ...

#define C_IN ...
#define T_A  ...
#define T_AAAA  ...
#define T_CNAME ...
#define T_MX  ...
#define T_NAPTR ...
#define T_NS  ...
#define T_PTR ...
#define T_SOA ...
#define T_SRV ...
#define T_TXT ...


/* ares_build.h */
typedef int... ares_socket_t;
typedef int... ares_socklen_t;
#define ARES_SUCCESS            0

/* Server error codes (ARES_ENODATA indicates no relevant answer) */
#define ARES_ENODATA            1
#define ARES_EFORMERR           2
#define ARES_ESERVFAIL          3
#define ARES_ENOTFOUND          4
#define ARES_ENOTIMP            5
#define ARES_EREFUSED           6

/* Locally generated error codes */
#define ARES_EBADQUERY          7
#define ARES_EBADNAME           8
#define ARES_EBADFAMILY         9
#define ARES_EBADRESP           10
#define ARES_ECONNREFUSED       11
#define ARES_ETIMEOUT           12
#define ARES_EOF                13
#define ARES_EFILE              14
#define ARES_ENOMEM             15
#define ARES_EDESTRUCTION       16
#define ARES_EBADSTR            17

/* ares_getnameinfo error codes */
#define ARES_EBADFLAGS          18

/* ares_getaddrinfo error codes */
#define ARES_ENONAME            19
#define ARES_EBADHINTS          20

/* Uninitialized library error code */
#define ARES_ENOTINITIALIZED    21          /* introduced in 1.7.0 */

/* ares_library_init error codes */
#define ARES_ELOADIPHLPAPI           22     /* introduced in 1.7.0 */
#define ARES_EADDRGETNETWORKPARAMS   23     /* introduced in 1.7.0 */

/* More error codes */
#define ARES_ECANCELLED         24          /* introduced in 1.7.0 */

/* Flag values */
#define ARES_FLAG_USEVC         ...
#define ARES_FLAG_PRIMARY       ...
#define ARES_FLAG_IGNTC         ...
#define ARES_FLAG_NORECURSE     ...
#define ARES_FLAG_STAYOPEN      ...
#define ARES_FLAG_NOSEARCH      ...
#define ARES_FLAG_NOALIASES     ...
#define ARES_FLAG_NOCHECKRESP   ...
#define ARES_FLAG_EDNS          ...

/* Option mask values */
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

/* Nameinfo flag values */
#define ARES_NI_NOFQDN                  ...
#define ARES_NI_NUMERICHOST             ...
#define ARES_NI_NAMEREQD                ...
#define ARES_NI_NUMERICSERV             ...
#define ARES_NI_DGRAM                   ...
#define ARES_NI_TCP                     0
#define ARES_NI_UDP                     ...
#define ARES_NI_SCTP                    ...
#define ARES_NI_DCCP                    ...
#define ARES_NI_NUMERICSCOPE            ...
#define ARES_NI_LOOKUPHOST              ...
#define ARES_NI_LOOKUPSERVICE           ...
/* Reserved for future use */
#define ARES_NI_IDN                     ...
#define ARES_NI_IDN_ALLOW_UNASSIGNED    ...
#define ARES_NI_IDN_USE_STD3_ASCII_RULES ...

/* Addrinfo flag values */
#define ARES_AI_CANONNAME               ...
#define ARES_AI_NUMERICHOST             ...
#define ARES_AI_PASSIVE                 ...
#define ARES_AI_NUMERICSERV             ...
#define ARES_AI_V4MAPPED                ...
#define ARES_AI_ALL                     ...
#define ARES_AI_ADDRCONFIG              ...
/* Reserved for future use */
#define ARES_AI_IDN                     ...
#define ARES_AI_IDN_ALLOW_UNASSIGNED    ...
#define ARES_AI_IDN_USE_STD3_ASCII_RULES ...
#define ARES_AI_CANONIDN                ...

#define ARES_AI_MASK ...
#define ARES_GETSOCK_MAXNUM ... /* ares_getsock() can return info about this
                                  many sockets */
/*
#define ARES_GETSOCK_READABLE(bits,num) (bits & (1<< (num)))
#define ARES_GETSOCK_WRITABLE(bits,num) (bits & (1 << ((num) + \
                                         ARES_GETSOCK_MAXNUM)))
*/

/* c-ares library initialization flag values */
#define ARES_LIB_INIT_NONE   ...
#define ARES_LIB_INIT_WIN32  ...
#define ARES_LIB_INIT_ALL    ...


/*
 * Typedef our socket type
 */
//typedef int ares_socket_t;
#define ARES_SOCKET_BAD ...


typedef void (*ares_sock_state_cb)(void *data,
                                   ares_socket_t socket_fd,
                                   int readable,
                                   int writable);

struct apattern;

/* NOTE about the ares_options struct to users and developers.

   This struct will remain looking like this. It will not be extended nor
   shrunk in future releases, but all new options will be set by ares_set_*()
   options instead of with the ares_init_options() function.

   Eventually (in a galaxy far far away), all options will be settable by
   ares_set_*() options and the ares_init_options() function will become
   deprecated.

   When new options are added to c-ares, they are not added to this
   struct. And they are not "saved" with the ares_save_options() function but
   instead we encourage the use of the ares_dup() function. Needless to say,
   if you add config options to c-ares you need to make sure ares_dup()
   duplicates this new option.

 */
struct ares_options {
  int flags;
  int timeout; /* in seconds or milliseconds, depending on options */
  int tries;
  int ndots;
  unsigned short udp_port;
  unsigned short tcp_port;
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
};

struct hostent;
struct timeval;
struct sockaddr;
struct ares_channeldata;

typedef struct ares_channeldata *ares_channel;

typedef void (*ares_callback)(void *arg,
                              int status,
                              int timeouts,
                              unsigned char *abuf,
                              int alen);

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

int ares_library_init(int flags);

void ares_library_cleanup(void);

const char *ares_version(int *version);

int ares_init(ares_channel *channelptr);

int ares_init_options(ares_channel *channelptr,
                                   struct ares_options *options,
                                   int optmask);

int ares_save_options(ares_channel channel,
                                   struct ares_options *options,
                                   int *optmask);

void ares_destroy_options(struct ares_options *options);

int ares_dup(ares_channel *dest,
                          ares_channel src);

void ares_destroy(ares_channel channel);

void ares_cancel(ares_channel channel);

/* These next 3 configure local binding for the out-going socket
 * connection.  Use these to specify source IP and/or network device
 * on multi-homed systems.
 */
void ares_set_local_ip4(ares_channel channel, unsigned int local_ip);

/* local_ip6 should be 16 bytes in length */
void ares_set_local_ip6(ares_channel channel,
                                     const unsigned char* local_ip6);

/* local_dev_name should be null terminated. */
void ares_set_local_dev(ares_channel channel,
                                     const char* local_dev_name);

void ares_set_socket_callback(ares_channel channel,
                                           ares_sock_create_callback callback,
                                           void *user_data);

void ares_send(ares_channel channel,
                            const unsigned char *qbuf,
                            int qlen,
                            ares_callback callback,
                            void *arg);

void ares_query(ares_channel channel,
                             const char *name,
                             int dnsclass,
                             int type,
                             ares_callback callback,
                             void *arg);

void ares_search(ares_channel channel,
                              const char *name,
                              int dnsclass,
                              int type,
                              ares_callback callback,
                              void *arg);

void ares_gethostbyname(ares_channel channel,
                                     const char *name,
                                     int family,
                                     ares_host_callback callback,
                                     void *arg);

int ares_gethostbyname_file(ares_channel channel,
                                         const char *name,
                                         int family,
                                         struct hostent **host);

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

int ares_fds(ares_channel channel,
                          fd_set *read_fds,
                          fd_set *write_fds);

int ares_getsock(ares_channel channel,
                              ares_socket_t *socks,
                              int numsocks);

struct timeval *ares_timeout(ares_channel channel,
                                          struct timeval *maxtv,
                                          struct timeval *tv);

void ares_process(ares_channel channel,
                               fd_set *read_fds,
                               fd_set *write_fds);

void ares_process_fd(ares_channel channel,
                                  ares_socket_t read_fd,
                                  ares_socket_t write_fd);

int ares_create_query(const char *name,
                                   int dnsclass,
                                   int type,
                                   unsigned short id,
                                   int rd,
                                   unsigned char **buf,
                                   int *buflen,
                                   int max_udp_size);

int ares_mkquery(const char *name,
                              int dnsclass,
                              int type,
                              unsigned short id,
                              int rd,
                              unsigned char **buf,
                              int *buflen);

int ares_expand_name(const unsigned char *encoded,
                                  const unsigned char *abuf,
                                  int alen,
                                  char **s,
                                  long *enclen);

int ares_expand_string(const unsigned char *encoded,
                                    const unsigned char *abuf,
                                    int alen,
                                    unsigned char **s,
                                    long *enclen);

/*
 * NOTE: before c-ares 1.7.0 we would most often use the system in6_addr
 * struct below when ares itself was built, but many apps would use this
 * private version since the header checked a HAVE_* define for it. Starting
 * with 1.7.0 we always declare and use our own to stop relying on the
 * system's one.
 */
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

struct ares_srv_reply {
  struct ares_srv_reply  *next;
  char                   *host;
  unsigned short          priority;
  unsigned short          weight;
  unsigned short          port;
  int                     ttl;
};

struct ares_mx_reply {
  struct ares_mx_reply   *next;
  char                   *host;
  unsigned short          priority;
  int                     ttl;
};

struct ares_txt_reply {
  struct ares_txt_reply  *next;
  unsigned char          *txt;
  size_t                  length;  /* length excludes null termination */
  int                     ttl;
};

/* NOTE: This structure is a superset of ares_txt_reply */
struct ares_txt_ext {
  struct ares_txt_ext      *next;
  unsigned char            *txt;
  size_t                   length;
  /* 1 - if start of new record
   * 0 - if a chunk in the same record */
  unsigned char            record_start;
  int                     ttl;
};

struct ares_naptr_reply {
  struct ares_naptr_reply *next;
  unsigned char           *flags;
  unsigned char           *service;
  unsigned char           *regexp;
  char                    *replacement;
  unsigned short           order;
  unsigned short           preference;
  int                      ttl;
};

struct ares_soa_reply {
  char        *nsname;
  char        *hostmaster;
  unsigned int serial;
  unsigned int refresh;
  unsigned int retry;
  unsigned int expire;
  unsigned int minttl;
  int          ttl;
};

/*
** Parse the buffer, starting at *abuf and of length alen bytes, previously
** obtained from an ares_search call.  Put the results in *host, if nonnull.
** Also, if addrttls is nonnull, put up to *naddrttls IPv4 addresses along with
** their TTLs in that array, and set *naddrttls to the number of addresses
** so written.
*/

int ares_parse_a_reply(const unsigned char *abuf,
                                    int alen,
                                    struct hostent **host,
                                    struct ares_addrttl *addrttls,
                                    int *naddrttls);

int ares_parse_aaaa_reply(const unsigned char *abuf,
                                       int alen,
                                       struct hostent **host,
                                       struct ares_addr6ttl *addrttls,
                                       int *naddrttls);

int ares_parse_ptr_reply(const unsigned char *abuf,
                                      int alen,
                                      const void *addr,
                                      int addrlen,
                                      int family,
                                      struct hostent **host,
                                      int *hostttl);

int ares_parse_ns_reply(const unsigned char *abuf,
                                     int alen,
                                     struct hostent **host);

int ares_parse_srv_reply(const unsigned char* abuf,
                                      int alen,
                                      struct ares_srv_reply** srv_out);

int ares_parse_mx_reply(const unsigned char* abuf,
                                      int alen,
                                      struct ares_mx_reply** mx_out);

int ares_parse_txt_reply_ext(const unsigned char* abuf,
                                      int alen,
                                      struct ares_txt_ext** txt_out);

int ares_parse_naptr_reply(const unsigned char* abuf,
                                        int alen,
                                        struct ares_naptr_reply** naptr_out);

int ares_parse_soa_reply(const unsigned char* abuf,
                                      int alen,
                                      struct ares_soa_reply** soa_out);

void ares_free_string(void *str);

void ares_free_hostent(struct hostent *host);

void ares_free_data(void *dataptr);

const char *ares_strerror(int code);

/* TODO:  Hold port here as well. */
struct ares_addr_node {
  struct ares_addr_node *next;
  int family;
  union {
    struct in_addr       addr4;
    struct ares_in6_addr addr6;
  } addr;
};

int ares_set_servers(ares_channel channel,
                                  struct ares_addr_node *servers);

/* Incomming string format: host[:port][,host[:port]]... */
int ares_set_servers_csv(ares_channel channel,
                                      const char* servers);

int ares_get_servers(ares_channel channel,
                                  struct ares_addr_node **servers);

const char *ares_inet_ntop(int af, const void *src, char *dst,
                                        ares_socklen_t size);

int ares_inet_pton(int af, const char *src, void *dst);

/* declare */
char* reverse_address(const char *ip_address, char *name);

""")

ffi.set_source("_pycares_cffi", """
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
# include <WinSock2.h>
#else
# include <sys/types.h>
# include <sys/socket.h>
# include <netdb.h> /* struct hostent */
# include <netinet/in.h> /* struct sockaddr_in/sockaddr_in6 */
#endif
#define CARES_STATICLIB 1 /* static link it */
#include <ares.h>
# include <nameser.h>

char* reverse_address(const char *ip_address, char *name)
{
    /*char name[128]; */
    unsigned long laddr, a1, a2, a3, a4;
    unsigned char *bytes;
    struct in_addr addr4;
    struct in6_addr addr6;

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
        return NULL;
    }

    return name;
}

""", libraries=(extra_libraries), include_dirs=[os.path.join(current_dir, "../../deps/c-ares/src"),], library_dirs=[os.path.join(current_dir, "../../deps/c-ares"),])


if __name__ == "__main__":
    ffi.compile(verbose=True)

