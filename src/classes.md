---
layout: single
classes: wide
title: Classes
sidebar:
  nav: "classes"
---

{% assign categories = site.data.classes | map: "category" | uniq %}

{% for category in categories %}
  <h2>{{ category }}</h2>

  <table>
    <tr>
      <th>Name</th>
      <th>Description</th>
    </tr>
    {% assign classes = site.data.classes | where: "category", category %}
    {% for class in classes %}
      <tr>
        <td>
          <a href="{% link {{ class.name | slugify }}.html %}">{{ class.name }}</a>
        </td>
        <td>{{ class.brief }}</td>
      </tr>
    {% endfor %}
  </table>
{% endfor %}