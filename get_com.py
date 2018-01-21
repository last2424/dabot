import deviantart

da = deviantart.Api("7398",
    "3a869a1d08967f442f1391cf9df9a93c")
print(da.browse_userjournals(username="nyamrianworkshop")['results'][0])