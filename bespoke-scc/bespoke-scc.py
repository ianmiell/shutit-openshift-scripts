import minishift

s1 = minishift.startup()

# Log in as admin
minishift.login_as_root(s1)

s1.send('oc delete scc cluster-admin-scc -n bespokesccprj || true')
s1.send('oc delete sa myclusteradminsa -n bespokesccprj || true')
s1.send('oc delete is bespokescc -n bespokesccprj || true')
s1.send('oc delete bc bespokescc -n bespokesccprj || true')
s1.send('oc delete dc bespokescc -n bespokesccprj || true')
s1.send('oc delete project bespokesccprj || true')
# Gap needed for some reason
s1.send("sleep 30 && oc adm new-project bespokesccprj --admin='developer'")

# Create custom SCC - this is restricted + cluster-admins
# Looked at privileged scc with 'oc edit scc privileged' and took groups item
s1.send_file('/tmp/scc.yaml',"""allowHostDirVolumePlugin: false
allowHostIPC: false
allowHostNetwork: false
allowHostPID: false
allowHostPorts: false
allowPrivilegedContainer: false
allowedCapabilities: []
apiVersion: v1
defaultAddCapabilities: []
fsGroup:
  type: MustRunAs
groups:
- system:cluster-admins
kind: SecurityContextConstraints
metadata:
  annotations:
    kubernetes.io/description: restricted denies access to all host features and requires
      pods to be run with a UID, and SELinux context that are allocated to the namespace.  This
      is the most restrictive SCC and it is used by default for authenticated users.
  creationTimestamp: 2017-09-15T15:13:40Z
  name: cluster-admin-scc
  resourceVersion: "275"
  selfLink: /api/v1/securitycontextconstraints/restricted
  uid: 74894f31-9a28-11e7-a15a-3e46e2387245
priority: null
readOnlyRootFilesystem: false
requiredDropCapabilities:
- KILL
- MKNOD
- SYS_CHROOT
- SETUID
- SETGID
runAsUser:
  type: MustRunAsRange
seLinuxContext:
  type: MustRunAs
supplementalGroups:
  type: RunAsAny
volumes:
- configMap
- downwardAPI
- emptyDir
- persistentVolumeClaim
- projected
- secret""")
s1.send('oc create -f /tmp/scc.yaml')
# Create a service account.
s1.send('oc create sa myclusteradminsa')
# Add the new custom SCC to this service account.
s1.send('oc adm policy add-scc-to-user cluster-admin-scc -z myclusteradminsa')

# TODO: Get the token for the sa
# TODO: Add the token as a secret
# TODO: Get the kubectl client and add to the dockerfile
# TODO: Use the kubectl client to create the kube config file
# TODO: Add the python libraries (pip) to the client

minishift.login_as_developer(s1)

# CREATE BUILD, AND ADD oc client
s1.send("""oc new-build --dockerfile 'FROM centos:7
RUN curl -L -s https://github.com/openshift/origin/releases/download/v3.6.0/openshift-origin-client-tools-v3.6.0-c4dd4cf-linux-64bit.tar.gz | tar -zxvf - && cp */oc /usr/local/bin
CMD sleep 999999' --to bespokescc:latest""")
s1.send('sleep 30')
s1.send('oc new-app --image-stream=bespokescc')
s1.send('sleep 30')
s1.send("""oc patch dc bespokescc -p '{"spec":{"template":{"spec":{"serviceAccountName": "myclusteradminsa"}}}}'""")
s1.login('''oc exec -ti $(oc get --no-headers pods | grep -v build | grep bespokescc | awk '{print $1}') bash''')
s1.pause_point('oc login https://openshift.default.svc.cluster.local')
s1.send('oc login https://openshift.default.svc.cluster.local')
s1.logout()
