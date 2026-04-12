TOKEN=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

echo "Creating private repository ohv-trail-dashboard..."
curl -s -X POST https://api.github.com/mgossman71/repos \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"ohv-trail-dashboard","private":true,"description":"Personal web application for browsing Minnesota OHV trail statuses","homepage":"http://oc1:8000"}'
