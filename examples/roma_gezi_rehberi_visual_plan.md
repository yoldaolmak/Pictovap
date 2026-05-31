# Roma Gezi Rehberi Visual Plan v1

Source page:
- https://yoldaolmak.com/roma-gezi-rehberi.html

Model goal:
- use this article as the pilot page for the visual memory system
- map each major heading to a visual slot
- later fill each slot from the Mac Photos asset index first

## Extracted Structure

### H1
- Roma Gezi Rehberi: Kolezyum’dan Vatikan’a Şehri Keşfetmek

### H2
- Roma Nerede
- Roma’da Kaç Gün Kalmalı
- Roma’ya Nasıl Gidilir
- Roma Gezi Rehberi: Kolezyum’dan Vatikan’a
- Roma’da Nerede Kalınır?
- Roma Gezilecek Yerler

### H3 under Roma’da Nerede Kalınır?
- Tarihi Merkez ve Kolezyum Çevresi
- Vatikan ve Prati Çevresi
- Trastevere — Şehrin Ruhu
- Termini Çevresi — Pratik ve Ekonomik
- Konfor öncelikliyse, bütçe ikinci plandaysa

## Slot Map

### slot_01
- heading: Roma Gezi Rehberi: Kolezyum’dan Vatikan’a Şehri Keşfetmek
- slot_type: hero_landmark
- visual_goal: define Rome instantly
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - broad Rome landmark scene
  - city-defining image
  - not a tight selfie
- first query seeds:
  - roma
  - rome landmark
  - kolezyum
  - vatikan

### slot_02
- heading: intro story near Trevi
- slot_type: intro_story
- visual_goal: personal Rome connection
- preferred_orientation: portrait or landscape
- recommended_format: flexible
- ideal_content:
  - personal but place-aware frame
  - Trevi, piazza, or historic center
- first query seeds:
  - trevi
  - roma merkez
  - kemal kaya rome

### slot_03
- heading: Roma Nerede
- slot_type: city_context
- visual_goal: geographic city feel
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - skyline
  - river
  - terrace view
  - wide city context
- avoid:
  - close portrait only

### slot_04
- heading: Roma’da Kaç Gün Kalmalı
- slot_type: planning_support
- visual_goal: walking tempo and city rhythm
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - street walking
  - route atmosphere
  - layered city scene

### slot_05
- heading: Roma’ya Nasıl Gidilir
- slot_type: transport_support
- visual_goal: optional support visual
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - airport
  - train
  - transit
- note:
  - can remain imageless if weak candidates only

### slot_06
- heading: Roma Gezi Rehberi: Kolezyum’dan Vatikan’a
- slot_type: landmark_pair
- visual_goal: article backbone
- preferred_orientation: landscape
- recommended_format: gallery_pair
- ideal_content:
  - one strong Colosseum frame
  - one Vatican or central Rome frame

### slot_07
- heading: Tarihi Merkez ve Kolezyum Çevresi
- slot_type: district_landmark
- visual_goal: Monti / Colosseum access feel
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - Colosseum area street
  - Monti texture

### slot_08
- heading: Vatikan ve Prati Çevresi
- slot_type: district_landmark
- visual_goal: calm, ordered Vatican district feel
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - Vatican exterior
  - Prati avenue
  - dome context

### slot_09
- heading: Trastevere — Şehrin Ruhu
- slot_type: district_atmosphere
- visual_goal: emotion and neighborhood texture
- preferred_orientation: portrait
- recommended_format: 4:5
- ideal_content:
  - narrow streets
  - ivy walls
  - restaurant life

### slot_10
- heading: Termini Çevresi — Pratik ve Ekonomik
- slot_type: district_practical
- visual_goal: transit convenience
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - station area
  - transport scene
- note:
  - use only if image quality is editorial enough

### slot_11
- heading: Konfor öncelikliyse, bütçe ikinci plandaysa
- slot_type: premium_stay_support
- visual_goal: refined Rome stay
- preferred_orientation: landscape
- recommended_format: 16:10
- ideal_content:
  - terrace
  - elegant facade
  - premium city view

### slot_12
- heading: Roma Gezilecek Yerler
- slot_type: section_backbone
- visual_goal: broad sightseeing overview
- preferred_orientation: landscape
- recommended_format: gallery_triptych
- ideal_content:
  - Colosseum
  - Pantheon / central square
  - Vatican / Trastevere

## Candidate Rules

- prefer `mac_photos` first
- prefer frames with recognizable place evidence
- penalize repeated selfies for consecutive slots
- prefer wide editorial compositions for H2 slots
- use portrait frames mainly for atmosphere sections like Trastevere
- if a slot has no strong photo, leave it empty instead of forcing a weak image

## Next Step

Run Mac Photos search against these seed queries:

- roma
- rome
- kolezyum
- colosseum
- trevi
- pantheon
- vatikan
- vatican
- trastevere
- prati
- termini
- monti
