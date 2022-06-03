const navBar = $("#mySidenav")
const divider = '<div class="dropdown-divider"></div>'
window.displayBoxIndex = -1

$(`a[href="${location.pathname}"].wrap_nav`).addClass("current");

navBar.on('mouseover', function () {
    $(this).addClass("wrap-nav-open")
})

navBar.on('mouseout', function () {
    $(this).removeClass("wrap-nav-open")
})

$('#search').on('input', function () {
    let search_result = $('#search-result')
    search_result.show()
    let query = $(this).val()
    let spinner = $('#search_spinner')
    if (query) {
        spinner.addClass("search_spinner_process")
            $.ajax({
                url: '/search/',
                data: {query: query, count: 5}
            }).done(function (response) {
                search_result.empty()
                window.displayBoxIndex = -1;
                $.each(response, function (k, v) {
                    if (k>0) {
                        search_result.append(divider)
                    }
                    let option = `<div data-url="${v.url}" class="display_box dropdown-custom-item">${v.title}</div>`
                    $(option).appendTo(search_result).on('click', function () {
                        $.ajax({
                            url: '/play/',
                            data: {query: this.dataset.url}
                        })
                    })
                })
                spinner.removeClass("search_spinner_process");
            })
    }
    else {
        spinner.removeClass("search_spinner_process")
        search_result.hide()
    }
})

$("#search").keyup(function(e)
{
    if (e.keyCode == 40)
    {
        Navigate(1);
    }
    if(e.keyCode==38)
    {
        Navigate(-1);
    }
});

var Navigate = function(diff) {
    displayBoxIndex += diff;
    var oBoxCollection = $(".display_box");
    if (displayBoxIndex >= oBoxCollection.length)
         displayBoxIndex = 0;
    if (displayBoxIndex < 0)
         displayBoxIndex = oBoxCollection.length - 1;
    var cssClass = "display_box_hover";
    oBoxCollection.removeClass(cssClass).eq(displayBoxIndex).addClass(cssClass);
}
