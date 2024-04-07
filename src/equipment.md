---
layout: single
classes: wide
title: Equipment
sidebar:
  nav: "character"
---

## Weapons

<div class="card-list">
  {% for card in site.data.equipment-weapons %}
    {% include power.html power=card %}
  {% endfor %}
</div>

## Armor

<div class="card-list">
  {% for card in site.data.equipment-armor %}
    {% include power.html power=card %}
  {% endfor %}
</div>