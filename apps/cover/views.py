# -*- coding: utf-8 -*-
#
# This file is part of FNP-Redakcja, licensed under GNU Affero GPLv3 or later.
# Copyright © Fundacja Nowoczesna Polska. See NOTICE for more information.
#
import os.path
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from catalogue.helpers import active_tab
from catalogue.models import Chunk
from cover.models import Image
from cover import forms


PREVIEW_SIZE = (216, 300)


def preview(request, book, chunk=None, rev=None):
    """Creates a cover image.

    If chunk and rev number are given, use version from given revision.
    If rev is not given, use publishable version.
    """
    import Image
    from librarian.cover import WLCover
    from librarian.dcparser import BookInfo

    chunk = Chunk.get(book, chunk)
    if rev is not None:
        try:
            revision = chunk.at_revision(rev)
        except Chunk.change_model.DoesNotExist:
            raise Http404
    else:
        revision = chunk.publishable()
        if revision is None:
            raise Http404
    xml = revision.materialize().encode('utf-8')

    try:
        info = BookInfo.from_string(xml)
    except:
        return HttpResponseRedirect(os.path.join(settings.STATIC_URL, "img/sample_cover.png"))
    cover = WLCover(info)
    response = HttpResponse(mimetype=cover.mime_type())
    image = cover.image().resize(PREVIEW_SIZE, Image.ANTIALIAS)
    image.save(response, cover.format)
    return response


@csrf_exempt
@require_POST
def preview_from_xml(request):
    from hashlib import sha1
    import Image
    from os import makedirs
    from lxml import etree
    from librarian.cover import WLCover
    from librarian.dcparser import BookInfo

    xml = request.POST['xml']
    try:
        info = BookInfo.from_string(xml.encode('utf-8'))
    except:
        return HttpResponse(os.path.join(settings.STATIC_URL, "img/sample_cover.png"))
    coverid = sha1(etree.tostring(info.to_etree())).hexdigest()
    cover = WLCover(info)

    cover_dir = 'cover/preview'
    try:
        makedirs(os.path.join(settings.MEDIA_ROOT, cover_dir))
    except OSError:
        pass
    fname = os.path.join(cover_dir, "%s.%s" % (coverid, cover.ext()))
    image = cover.image().resize(PREVIEW_SIZE, Image.ANTIALIAS)
    image.save(os.path.join(settings.MEDIA_ROOT, fname))
    return HttpResponse(os.path.join(settings.MEDIA_URL, fname))


@active_tab('cover')
def image(request, pk):
    image = get_object_or_404(Image, pk=pk)

    if request.user.has_perm('cover.change_image'):
        if request.method == "POST":
            form = forms.ImageEditForm(request.POST, instance=image)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(image.get_absolute_url())
        else:
            form = forms.ImageEditForm(instance=image)
        editable = True
    else:
        form = forms.ReadonlyImageEditForm(instance=image)
        editable = False

    return render(request, "cover/image_detail.html", {
        "object": image,
        "form": form,
        "editable": editable,
    })


@active_tab('cover')
def image_list(request):
    objects = Image.objects.all()
    enable_add = request.user.has_perm('cover.add_image')
    return render(request, "cover/image_list.html", {
        'object_list': Image.objects.all(),
        'can_add': request.user.has_perm('cover.add_image'),
    })


@permission_required('cover.add_image')
@active_tab('cover')
def add_image(request):
    form = ff = None
    if request.method == 'POST':
        if request.POST.get('form_id') == 'flickr':
            ff = forms.FlickrForm(request.POST)
            if ff.is_valid():
                form = forms.ImageAddForm(ff.cleaned_data)
        else:
            form = forms.ImageAddForm(request.POST)
            if form.is_valid():
                obj = form.save()
                return HttpResponseRedirect(obj.get_absolute_url())
    if form is None:
        form = forms.ImageAddForm()
    if ff is None:
        ff = forms.FlickrForm()
    return render(request, 'cover/add_image.html', {
            'form': form,
            'ff': ff,
        })
