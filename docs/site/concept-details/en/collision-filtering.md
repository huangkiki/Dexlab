## How contype and conaffinity select collision pairs

`contype` declares the geom's collision categories and `conaffinity` declares which categories it accepts. A dynamically generated pair passes the mask check if either geom's `contype` has a bit in common with the other's `conaffinity`. Also check contact flags, body exclusions and parent filtering. An explicit `contact/pair` follows a separate pairing path.

If a pad approaching an object never produces a contact for the intended pair, hold a pose with verified overlap between the collision surfaces and look for the two geoms in `data.contact`. If the record is still missing, check collision filtering first. If records go missing only at speed, compare separation and first-contact time at a smaller timestep.

{ref}`Find contact parameters by symptom <contact-tuning>`
