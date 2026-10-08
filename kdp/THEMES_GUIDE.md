# Writing KDP book themes (Tiny Comet Prints)

Each theme becomes one 64-page paperback coloring & activity book for kids ages 4-8
(cover, title page, 30 activity pages printed single-sided, thank-you page). The daily GitHub
Action builds the lowest-numbered file in `kdp/themes/queue/` and moves it to `kdp/themes/done/`.

## File
`kdp/themes/queue/NNN-slug.json`. NNN continues from the highest number in `queue/` and `done/`.
Run `python3 kdp/engine/validate.py kdp/themes/queue/NNN-slug.json` until it prints OK, and do a
test build: `python3 kdp/engine/build.py kdp/themes/queue/NNN-slug.json --out /tmp/test` (must finish without errors).

## Fields
| field | rules |
|---|---|
| slug | lowercase-with-dashes, unique (not used in `done/` or `kdp/catalog.json`) |
| title | 22 characters max (it is the big cover title). The book title on Amazon becomes "<title> Coloring & Activity Book" |
| cover_line | always "Coloring & Activity Book" |
| kdp_subtitle | 120-180 chars, keyword-rich, ends with "for Kids Ages 4-8" |
| scene | one of: meadow, farm, forest, jungle, town, party, snow, ocean, space |
| place | short phrase used in page instructions, e.g. "the garden" |
| characters | 5-6 names from the CHARACTER list. First one is the title-page hero |
| cover_characters | 3 of the characters (big, medium, small on the cover) |
| props | 5-6 names from the PROP list that fit the theme |
| cover_props | 2 props (bottom corners of the cover) |
| maze_goals | 3 props or characters the maze hero walks to |
| dot_shapes | up to 4 of: star, heart, fish, balloon, apple, house, rocket, egg |
| words | 8-12 UPPERCASE single words (letters only, 3-9 letters) for tracing and word search; words that match a character/prop name get its picture |
| sky_colour | optional crayon name for the colour-by-number sky (default lightblue) |
| back_headline | short, fun, under 30 chars |
| back_lines | 2 lines, each under 55 chars |
| description | Amazon HTML (`<b>`, `<br>`, `<ul><li>`), follow the pattern of existing themes; no claims you can't keep, no other brands |
| keywords | exactly 7, each under 50 chars, phrases buyers type; no brand or trademark names (no Disney, Paw Patrol, Pokemon, Bluey...) |
| categories | 3 Amazon browse paths (first is always the Coloring Books category) |
| price | "$7.99" unless there's a reason |
| spine_colour | hex colour that fits the theme |

## Available CHARACTERS
cat, dog, bunny, bear, panda, pig, cow, sheep, fox, mouse, lion, elephant, monkey, koala, raccoon,
hedgehog, capybara, reindeer, unicorn, dragon, dino, frog, chick, duck, owl, penguin, fish, whale,
octopus, crab, turtle, starfish, bee, ladybug, butterfly, snail, caterpillar, robot, snowman

## Available PROPS
tree, pine, flower, mushroom, barn, house, apple, carrot, strawberry, cupcake, donut, icecream, cake,
balloon, gift, xmastree, candycane, star, heart, sun, moon, planet, rocket, car, truck, train, plane,
boat, shell, seaweed, coral, rock, snowflake, pumpkin, egg, fence, bone, cookie, lollipop, umbrella

(No people, no licensed characters. If a theme needs something not in these lists, pick a different theme.)

## Choosing themes (research first)
- Kids 4-8 is the biggest coloring market. Winning books use a clear subject plus a twist
  ("capybara bakery", "space pets", "woodland picnic") instead of a generic one ("animals").
- Seasonal: publish ~6-8 weeks before the peak. Rough calendar: Valentine's by early January,
  Easter/spring by late February, summer/road-trip by April, back to school by June,
  Halloween by August, Christmas by September-October, winter by late November.
- Mix: about 1 seasonal theme in every 3, the rest evergreen.
- Never repeat a theme or near-duplicate already in `done/`, `queue/` or the older titles
  (Solar System, Christmas, Dinosaur coloring & activity books).
- Check that the subject is not a trademark.
