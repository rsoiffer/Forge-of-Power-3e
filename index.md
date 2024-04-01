---
layout: single
classes: wide
sidebar:
  nav: "classes"
---

# Welcome

This is a work-in-progress site for the tabletop rpg system Forge of Power, 3rd edition.

{% for s in site.data.classes %}
  <h2>{{ s.name }}</h2>
  <p>{{ s.brief }}</p>
{% endfor %}
