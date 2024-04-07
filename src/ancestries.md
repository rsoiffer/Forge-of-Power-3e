---
layout: single
classes: wide
title: Ancestries
sidebar:
  nav: "character"
---

<div class="card-list">
  {% for card in site.data.ancestries %}
    {% include power.html power=card %}
  {% endfor %}
</div>