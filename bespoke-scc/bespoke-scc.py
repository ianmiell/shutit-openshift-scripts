import minishift

s1 = minishift.startup()

s1.send('oc delete project bespokesccprj || /bin/true')
s1.send('oc adm new-project bespokesccprj')
