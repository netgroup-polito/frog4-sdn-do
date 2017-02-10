## Step-by-step Validation

### Data model validation

To validate the Data Model itself:

    $ pyang netgroup-domain.yang netgroup-if-side.yang netgroup-neighbor.yang openconfig/iana-if-type.yang augment-oc-adapter/*.yang -p .:./ietf:./openconfig/:./augment-oc-adapter/
    
If the data model is valid, no output will be returned.

You can also print a tree view of the data model; to do this. run:

    $ pyang -f tree netgroup-domain.yang netgroup-if-side.yang netgroup-neighbor.yang openconfig/iana-if-type.yang augment-oc-adapter/*.yang -p .:./ietf:./openconfig/:./augment-oc-adapter/

### XML instance validation

First of all, the YANG model has to be converted into a dsdl model.

    $ cd data_model
    $ yang2dsdl -t data netgroup-domain.yang netgroup-if-side.yang netgroup-neighbor.yang openconfig/iana-if-type.yang augment-oc-adapter/*.yang -p .:./ietf:./openconfig/:./augment-oc-adapter/
    
At this point you should have three new files in your working directory (.rng, .sch and .dsrl).
To validate the XML instance using the generated files, run:

    $ yang2dsdl -t data -s -j -b netgroup-domain_netgroup-if-side_netgroup-neighbor_iana-if-type_netgroup-if-capabilities_netgroup-if-ethernet_netgroup-if-gre_netgroup-if-ip_netgroup-vlan -v di_data.xml
    
where ***di_data.xml*** is the file name of the XML instance to be validated.

If no errors are returned, the instance is definitively valid.
 
Now it's possible to remove all dsdl generated files:

    $ rm *.dsrl *.rng *.sch

### JSON instance validation

To validate a JSON instance, we need to convert it to an XML through pyang.

To do this, we need to generate jtox driver throug a pyang plugin:

    $ pyang netgroup-domain.yang netgroup-if-side.yang netgroup-neighbor.yang openconfig/iana-if-type.yang augment-oc-adapter/*.yang -p .:./ietf:./openconfig/:./augment-oc-adapter/ -f jtox -o di.jtox
    
Then convert the JSON to an XML:

    $ json2xml -o di_data.xml di.jtox di_data.json
    
where ***di_data.json*** is the name of the JSON instance to be validated.

Remove the jtox generated file:

    $ rm di.jtox

At this point you can validate the XML instance as explained on the previous section.