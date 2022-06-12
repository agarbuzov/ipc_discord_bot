let track_list = $('form#track_list')
let list_buttons = $('div#list_buttons', track_list)
let current_request

function add_row() {
    let track_input = $('div#track_input:last', track_list)
    let track_input_clone = track_input.clone()
    let span = $('span.input-group-text', track_input_clone)
    let search_result = $('div.dropdown-menu', track_input_clone)
    let index = parseInt(span.text())
    $('input', track_input_clone).val('')
    search_result.hide()
    search_result.empty()
    span.text(++index)
    track_input_clone.insertBefore(list_buttons)
}

function remove_row () {
    $('div#track_input:last').remove()
}

function rebuild_order () {
    let inputs = $('div[id^="track_input"]', track_list)
    inputs.each(
        function (index, element) {
            $('span', element).text(index+1)
        }
    )
}

$('#inputImageFile').on('change', function (e) {
    let output = $('#filePreview')
    let url = URL.createObjectURL(e.target.files[0])
    output.attr('src', url)
    output.on('load', function () {
        URL.revokeObjectURL(url)
    })
})

track_list.on('input', 'input.track-input', function() {
    if ($(this).val() && $(this).is($('.track-input:last'))) {
        add_row()
    }
    else if (!$(this).val() && $(this).is($('.track-input:last').parent().prev().find('.track-input'))) {
        remove_row()
    }
    else if (!$(this).val() && !$(this).is($('.track-input:last').parent().prev().find('.track-input'))) {
        $(this).parent().remove()
        rebuild_order()
    }
})

$('body').on('input', 'input.yt-search', function () {
    if (current_request) {
        current_request.abort()
    }
    let track = $(this)
    let track_input = $(this).parent()
    let query = track.val()
    let spinner = track_input.find('div[class*=spinner]')
    let search_result = track_input.find('div.dropdown-menu')
    if (query) {
        spinner.show()
        current_request = $.ajax({
            url: '/search/',
            data: {query: query, count: 5}
        }).done(function (response) {
            search_result.empty()
            window.displayBoxIndex = -1;
            if (response) {
                $.each(response, function (k, v) {
                    if (k>0) {
                        search_result.append(divider)
                    }
                    let option = `<div data-url="${v.url}" data-duration="${v.duration}" class="display_box dropdown-custom-item">${v.title} (${v.duration})</div>`
                    $(option).appendTo(search_result).on('click', function () {
                        track.val($(this).text())
                        track.data("duration", $(this).data("duration"))
                        track.data("url", $(this).data("url"))
                        search_result.hide()
                        search_result.empty()
                    })
                })
                search_result.show()
            }
            spinner.hide()
        })
    }
    else {
        spinner.hide()
        search_result.hide()
    }
})

track_list.on('focus', 'input.track-input', function() {
    $('input[name="track"]').not(this).each(function (index, element) {
        let search_result = $(element).parent().find('div.dropdown-menu')
        let spinner = $(element).parent().find('div[class*=spinner]')
        spinner.hide()
        search_result.hide()
        search_result.empty()
        current_request.abort()
    })
})


track_list.on('submit', function (e) {
    e.preventDefault()
    let name = $('input[name="name"]', this).val()
    let cover = $('input[name="cover"]', this).prop('files')[0]
    console.log(cover)
    let form_data = new FormData()
    let data = []
    $('div#track_input', track_list).each(function (index, element) {
        let track = $('input[name="track"]', element)
        data.push({"title": track.val(), "url": track.data("url"), "duration": track.data("duration")})
    })
    console.log(JSON.stringify(data))
    form_data.append("tracks", JSON.stringify(data))
    form_data.append("name", name)
    form_data.append("cover", cover)
    $.ajax({
        url: '/playlists/create/',
        data: form_data,
        processData: false,
        contentType: false,
        type: 'POST',
        dataType: "json",
        success: function (data) {
            console.log(data)
            window.location.href = data;
        },
        error: function (data) {
            console.log(data)
            // window.location.href = data.redirect;
        }
    });
})