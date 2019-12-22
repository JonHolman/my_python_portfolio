#!/usr/bin/env bash

sls info $@ -v | grep 'UserPoolClientId\|UserPoolId\|IdentityPoolId\|ServiceEndpoint\|AttachmentsBucketName'
