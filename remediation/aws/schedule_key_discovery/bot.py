import logging

def run(ctx):
    # SRN of the resource in the ticket
    object_srn = ctx.resource_srn

    # Create GraphQL client
    graphql_client = ctx.graphql_client()

    # options used in creating the data classification jobs for keys and secrets
    outputMode = "FINGERPRINT" # FINGERPRINT or OBJECT
    includeSamples = "true" # true or false
    scanMode = "FULL_SCAN" # FULL_SCAN, PARTIAL_SCAN or QUICK_SCAN
    classifiers = " AWSACCESSKEY, AWSSECRETKEY, AZURECLIENTSECRET, AZURESAS, AZURESTORAGEACCOUNTKEY, ENCRYPTIONKEY, GCPAPIKEY, GCPSERVICEACCOUNTKEY "
    encryptionEnabled = "false" # true or false
    # comment out next line if encryptionEnabled is false
    # public key needs to have carriage returns removed and replaced with \\n
    #publicKey ="-----BEGIN PUBLIC KEY-----\\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA5//KZA2xGUfTV8ohNOAj\\ny6ovDomGqL8Hq5g91vaLs9HfVIR8lrviP9S30y9KWPVWZ/3LWxLzN2uz8OSfK0JS\\nYiCCGdsYa3WppsSlSgMiI9uhDXJpgyBKNoKQcyZR67Bpbtj7/lR4kT6S3kNbIDNf\\nzO/dG4G9MGmdEE0A2wUgCKLHIMH7IoL4dfaSYW4eNcW+uxwX/pnUHWtLAlUFUel1\\np/LDUhjzEuQfw7MfLGHos6h54R+MaY+6OBd+NL6LKswlDwatMK+iu7BLTz3NP6GP\\nZ53n7yKrEs8vHmmTPRTqdEq+EtTtuKmF36j9NJm/t+krhhCqcAuGtyJT2FaBP5kE\\nsQIDAQAB\\n-----END PUBLIC KEY-----"

    # Mutation for schedule Data Classification
    mutation = ( 'mutation dc {' +
                 'CreateDataClassificationConfig (input: {'+
                 ' enabled:true' +
                 ' targetSrn: "' + object_srn + '" ' +
                 ' jobInfo: {' +
                    ' outputMode: '  + outputMode +
                    ' includeSamples: ' + includeSamples +
                    ' scanMode: '  + scanMode +
                    ' classifiers:  [ ' + classifiers + ' ]' +
                    ' encryptionEnabled: ' + encryptionEnabled
              )

    if 'publicKey' in locals():
        mutation += (
                    ' publicKey: "' + publicKey + '"'
        )

    mutation += ( ' }' +
               '}){srn}' +
               '}'
              )

    #variables can be blank because they are put directly into the mutation
    variables = {}

    # Schedule Data Classification job on object_srn
    logging.info('Schedule Data Classification on: {}'.format(object_srn))
    graphql_client.query(mutation, variables)
