from asgiproxy.config import BaseURLProxyConfigMixin, ProxyConfig


class ExampleComProxyConfig(BaseURLProxyConfigMixin, ProxyConfig):
    upstream_base_url = "http://example.com"
    rewrite_host_header = "example.com"
