(function($) {
    jQuery.fn.lazyload = function(pattern, options) {
        var settings = {
            threshold: 0,
            scrollThreshold: 300,
            placeholder: 'loading...',
            checkInterval: 2000
        };
        
        if (options) {
            $.extend(settings, options);
        }
        
        var container = this;
        container.data('lastScroll', -10000);
        
        function aboveViewport(container, element, threshold) {
            return $(container).offset().top >= $(element).offset().top + $(element).height() + threshold;
        }
        
        function belowViewport(container, element, threshold) {
            return $(container).offset().top + $(container).height() + threshold <= $(element).offset().top;
        }
        
        function checkScroll() {
            if (Math.abs(container.scrollTop() - container.data('lastScroll')) > settings.scrollThreshold) {
                container.data('lastScroll', container.scrollTop());
                
                $(pattern, container).each(function() {
                    if (aboveViewport(container, this, settings.threshold)
                        || belowViewport(container, this, settings.threshold)) {
                        $(this).html(settings.placeholder);
                    } else {
                        $(this).html('<img src="' + $(this).attr('src') + '" width="' + $(this).width() + '" />');
                    }
                })
            }
            setTimeout(checkScroll, settings.checkInterval);
        }
        
        checkScroll();
    };
})(jQuery);