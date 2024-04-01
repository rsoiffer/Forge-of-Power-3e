# frozen_string_literal: true

module CustomTags
  class IconTag < Liquid::Tag # rubocop:disable Style/Documentation
    include Jekyll::Filters::URLFilters

    def initialize(tag_name, text, tokens)
      super
      @text = text.strip
    end

    def render(context)
      @context = context
      @my_text = Liquid::Template.parse(@text).render(@context)
      "<img title=\"#{@my_text}\" class=\"inline-icon\" src=\"assets/svg/#{Jekyll::Utils.slugify(@my_text)}.svg\">"
    end
  end

  class ReferenceTag < Liquid::Tag # rubocop:disable Style/Documentation
    include Jekyll::Filters::URLFilters

    def initialize(tag_name, text, tokens)
      super
      @text = text.strip
    end

    def render(context)
      @context = context
      url = relative_url("#{Jekyll::Utils.slugify(@text)}.html")
      "<a href=\"#{url}\">#{@text}</a>"
    end
  end

  class TraitTag < Liquid::Tag # rubocop:disable Style/Documentation
    include Jekyll::Filters::URLFilters

    def initialize(tag_name, text, tokens)
      super
      @text = text.strip
    end

    def render(context)
      @context = context
      @my_text = Liquid::Template.parse(@text).render(@context)
      all_traits = @context.registers[:site].data['traits'].values.reduce(:merge)
      print("Warning: unknown trait \"#{@my_text}\"\n") unless all_traits.key?(@my_text)
      url = relative_url("traits.html##{Jekyll::Utils.slugify(@my_text)}")
      "<span class=\"trait\"><a href=\"#{url}\">#{@my_text}</a></span>"
    end
  end

  class RollMeOneTag < Liquid::Tag # rubocop:disable Style/Documentation
    def initialize(tag_name, text, tokens)
      super
      @text = text.strip
    end

    def render(context)
      @context = context
      "<div class=\"roll-me-one\" data-table=\"#{@text}\"></div>"
    end
  end
end

Liquid::Template.register_tag('icon', CustomTags::IconTag)
Liquid::Template.register_tag('ref', CustomTags::ReferenceTag)
Liquid::Template.register_tag('trait', CustomTags::TraitTag)
Liquid::Template.register_tag('roll_me_one', CustomTags::RollMeOneTag)

module CustomFilters
  module ProcessFilter # rubocop:disable Style/Documentation
    def process(input)
      input = Liquid::Template.parse(input.to_s).render(@context)

      converter = Jekyll::Converters::Markdown::LinkerProcessor.new(@context.registers[:site].config)

      converter.convert(input)
    end

    def process_inline(input)
      process(input)[3...-5]
    end
  end
end

class Jekyll::Converters::Markdown::LinkerProcessor # rubocop:disable Style/Documentation
  def initialize(config)
    @converter = Jekyll::Converters::Markdown::KramdownParser.new(config)
  end

  def convert(content) # rubocop:disable Metrics/AbcSize,Metrics/MethodLength
    new_content = content.gsub(/{[^{}]*}/) do |s|
      text = s[1..-2].strip
      slug_text = Jekyll::Utils.slugify(text)

      get_map = lambda { |map_name|
        map_name.split('/').reduce(Jekyll.sites[0].data) do |m, part|
          m[part]
        end
      }

      m = {}
      m['conditions'] = "[#{text}](conditions.html##{slug_text})"

      matches =
        m.map do |val|
          val[1] if get_map[val[0]].find do |k, _v|
            Jekyll::Utils.slugify(k) == slug_text
          end
        end.compact

      matches.first || begin
        print("Warning: could not resolve link to text \"#{text}\"\n")
        "***#{text}***"
      end
    end.gsub(/\[\[[^\[\]]*\]\]/) do |s| # rubocop:disable Style/MultilineBlockChain
      text = s[2..-3].strip
      all_traits = Jekyll.sites[0].data['traits'].values.reduce(:merge)
      print("Warning: unknown trait \"#{text}\"\n") unless all_traits.key?(text)
      url = "traits.html##{Jekyll::Utils.slugify(text)}"
      "<span class=\"trait\"><a href=\"#{url}\">#{text}</a></span>"
    end
    @converter.convert(new_content)
  end
end

Liquid::Template.register_filter(CustomFilters::ProcessFilter)
