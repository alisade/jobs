# CHG-7781 Istio 1.25.2 -> 1.27.1 canary upgrade (eks-prod-use1-b), executed 2026-10-06

1. 18:05 `istioctl install -f iop-1-27-1.yaml --set revision=1-27-1` -> istiod-1-27-1 Ready
2. 18:20 Relabelled namespaces to the new revision and rolled their workloads:
   - mcp-tools        `kubectl label ns mcp-tools istio.io/rev=1-27-1 istio-injection-`
   - payments-api     `kubectl label ns payments-api istio.io/rev=1-27-1 --overwrite`
   - istio-ingress    (gateway Helm release bumped to 1.27.1)
   Verified with `istioctl proxy-status`: all proxies on 1.27.1.
3. 19:10 `istioctl uninstall --revision default` (removes the 1.25.2 istiod and its
   injector webhook `istio-sidecar-injector`).
4. 19:15 Smoke test: ingress -> payments-api 200. Closed.

Note from the CHG template: "List every namespace with mesh workloads:
`kubectl get ns -L istio-injection -L istio.io/rev`." (not attached)
