var style_cookie;

/* IE/Opera fix, because they need to go learn a book on how to use indexOf with arrays */
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function(elt /*, from*/) {
	var len = this.length;

	var from = Number(arguments[1]) || 0;
	from = (from < 0)
		 ? Math.ceil(from)
		 : Math.floor(from);
	if (from < 0)
	  from += len;

	for (; from < len; from++) {
	  if (from in this &&
		  this[from] === elt)
		return from;
	}
	return -1;
  };
}

/**
*
*  UTF-8 data encode / decode
*  http://www.webtoolkit.info/
*
**/

var Utf8 = {

	// public method for url encoding
	encode : function (string) {
		string = string.replace(/\r\n/g,"\n");
		var utftext = "";

		for (var n = 0; n < string.length; n++) {

			var c = string.charCodeAt(n);

			if (c < 128) {
				utftext += String.fromCharCode(c);
			}
			else if((c > 127) && (c < 2048)) {
				utftext += String.fromCharCode((c >> 6) | 192);
				utftext += String.fromCharCode((c & 63) | 128);
			}
			else {
				utftext += String.fromCharCode((c >> 12) | 224);
				utftext += String.fromCharCode(((c >> 6) & 63) | 128);
				utftext += String.fromCharCode((c & 63) | 128);
			}

		}

		return utftext;
	},

	// public method for url decoding
	decode : function (utftext) {
		var string = "";
		var i = 0;
		var c = c1 = c2 = 0;

		while ( i < utftext.length ) {

			c = utftext.charCodeAt(i);

			if (c < 128) {
				string += String.fromCharCode(c);
				i++;
			}
			else if((c > 191) && (c < 224)) {
				c2 = utftext.charCodeAt(i+1);
				string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
				i += 2;
			}
			else {
				c2 = utftext.charCodeAt(i+1);
				c3 = utftext.charCodeAt(i+2);
				string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
				i += 3;
			}

		}

		return string;
	}

}

function replaceAll( str, from, to ) {
	var idx = str.indexOf( from );
	while ( idx > -1 ) {
		str = str.replace( from, to );
		idx = str.indexOf( from );
	}
	return str;
}

function insert(text) {
	var textarea=document.forms.postform.message;
	if(textarea) {
		if(textarea.createTextRange && textarea.caretPos) { // IE 
			var caretPos=textarea.caretPos;
			caretPos.text=caretPos.text.charAt(caretPos.text.length-1)==" "?text+" ":text;
		} else if(textarea.setSelectionRange) { // Firefox 
			var start=textarea.selectionStart;
			var end=textarea.selectionEnd;
			textarea.value=textarea.value.substr(0,start)+text+textarea.value.substr(end);
			textarea.setSelectionRange(start+text.length,start+text.length);
		} else {
			textarea.value+=text+" ";
		}
		textarea.focus();
	}
}

function quote(b, a) { 
	var v = eval("document." + a + ".message");
	v.value += ">>" + b + "\n";
	v.focus();
}

function checkhighlight() {
	var match;

	if(match=/#i([0-9]+)/.exec(document.location.toString()))
	if(!document.forms.postform.message.value)
	insert(">>"+match[1]);

	if(match=/#([0-9]+)/.exec(document.location.toString()))
	highlight(match[1]);
}

function highlight(post, checknopage) {
	if (checknopage && ispage) {
		return;
	}
	var cells = document.getElementsByTagName("td");
	for(var i=0;i<cells.length;i++) if(cells[i].className == "highlight") cells[i].className = "reply";

	var reply = document.getElementById("reply" + post);
	if(reply) {
		reply.className = "highlight";
		var match = /^([^#]*)/.exec(document.location.toString());
		document.location = match[1] + "#" + post;
	}
}

function expandimg(post_id, img_url, thumb_url, img_w, img_h, thumb_w, thumb_h) {
  var img_cont = document.getElementById("thumb" + post_id);
  var img;
  
  for(var i = 0; i < img_cont.childNodes.length; i++)
    if(img_cont.childNodes[i].nodeName == "IMG")
      img = img_cont.childNodes[i];
  
  if(img) {
    var new_img = document.createElement("img");
    new_img.setAttribute("class", "thumb");
    new_img.setAttribute("className", "thumb");
    new_img.setAttribute("alt", "" + post_id);
    
    if( (img.getAttribute("width") == ("" + thumb_w)) && (img.getAttribute("height") == ("" + thumb_h)) ) {
      // thumbnail -> fullsize
      new_img.setAttribute("src", "" + img_url);
      new_img.setAttribute("width", "" + img_w);
      new_img.setAttribute("height", "" + img_h);
    } else {
      // fullsize -> thumbnail
      new_img.setAttribute("src", "" + thumb_url);
      new_img.setAttribute("width", "" + thumb_w);
      new_img.setAttribute("height", "" + thumb_h);
    }
    
    while(img_cont.lastChild)
      img_cont.removeChild(img_cont.lastChild);
    
    img_cont.appendChild(new_img);
  }
} 

function get_password(name) {
	var pass = getCookie(name);
	if(pass) return pass;

	var chars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
	var pass='';

	for(var i=0;i<8;i++) {
		var rnd = Math.floor(Math.random()*chars.length);
		pass += chars.substring(rnd, rnd+1);
	}
	set_cookie(name, pass, 365);
	return(pass);
}

function getCookie(name) {
	with(document.cookie) {
		var regexp=new RegExp("(^|;\\s+)"+name+"=(.*?)(;|$)");
		var hit=regexp.exec(document.cookie);
		if(hit&&hit.length>2) return Utf8.decode(unescape(replaceAll(hit[2],'+','%20')));
		else return '';
	}
}

function set_cookie(name,value,days) {
	if(days) {
		var date=new Date();
		date.setTime(date.getTime()+(days*24*60*60*1000));
		var expires="; expires="+date.toGMTString();
	} else expires="";
	document.cookie=name+"="+value+expires+"; path=/";
}

function set_stylesheet(styletitle) {
	set_cookie(style_cookie,styletitle,365);

	var links=document.getElementsByTagName("link");
	var found=false;
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		
		if(rel.indexOf("style")!=-1&&title) {
			links[i].disabled=true; // IE needs this to work. IE needs to die.
			if(styletitle==title) { links[i].disabled=false; found=true; }
		}
	}
	if(!found) set_preferred_stylesheet();
}

function set_preferred_stylesheet() {
	var links=document.getElementsByTagName("link");
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		if(rel.indexOf("style")!=-1&&title) links[i].disabled=(rel.indexOf("alt")!=-1);
	}
}

function get_active_stylesheet() {
	var links=document.getElementsByTagName("link");
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		if(rel.indexOf("style")!=-1&&title&&!links[i].disabled) return title;
	}
	
	return null;
}

function get_preferred_stylesheet() {
	var links=document.getElementsByTagName("link");
	for(var i=0;i<links.length;i++) {
		var rel=links[i].getAttribute("rel");
		var title=links[i].getAttribute("title");
		if(rel.indexOf("style")!=-1&&rel.indexOf("alt")==-1&&title) return title;
	}
	
	return null;
}

function delandbanlinks() {
	if (typeof pyib_staff == "undefined") return;
	
	var dnbelements = document.getElementsByTagName('span');
	var dnbelement;
	var dnbinfo;
	for(var i=0;i<dnbelements.length;i++){
		dnbelement = dnbelements[i];
		if (dnbelement.getAttribute('class')) {
			if (dnbelement.getAttribute('class').substr(0, 3) == 'dnb') {
				dnbinfo = dnbelement.getAttribute('class').split('|');
				var newhtml = '&#91;<a href="' + cgi_url + 'manage/delete/' + dnbinfo[1] + '/' + dnbinfo[2] + '" title="Delete" onclick="return confirm(\'Are you sure you want to delete this post/thread?\');">D<\/a>&nbsp;<a href="' + cgi_url + 'manage/delete/' + dnbinfo[1] + '/' + dnbinfo[2] + '?ban=true" title="Delete &amp; Ban" onclick="return confirm(\'Are you sure you want to delete and ban the poster of this post/thread?\');">&amp;<\/a>&nbsp;<a href="' + cgi_url + 'manage/ban/' + dnbinfo[1] + '/' + dnbinfo[2] + '" title="Ban">B<\/a>';
				if (dnbinfo[3] == 'y') {
				  newhtml += '&nbsp;<a href="' + cgi_url + 'manage/modbrowse/' + dnbinfo[1] + '/' + dnbinfo[2] + '" title="Modbrowse">M<\/a>';
				}
				newhtml += '&#93;';
				
				dnbelements[i].innerHTML = newhtml;
			}
		}
	}
}

function togglethread(threadid) {
  if (hiddenthreads.toString().indexOf(threadid) !== -1) {
    document.getElementById('unhidethread' + threadid).style.display = 'none';
    document.getElementById('thread' + threadid).style.display = 'block';
    hiddenthreads.splice(hiddenthreads.indexOf(threadid), 1);
  } else {
    document.getElementById('unhidethread' + threadid).style.display = 'block';
    document.getElementById('thread' + threadid).style.display = 'none';
    hiddenthreads.push(threadid);
  }
  set_cookie('hiddenthreads', hiddenthreads.join('!'), 30);
  return false;
}

function set_inputs(id) {
	if (document.getElementById(id)) {
		with(document.getElementById(id)) {
			if(!name.value) name.value = getCookie("pyib_name");
			if(!email.value) email.value = getCookie("pyib_email");
			if(!password.value) password.value = get_password("pyib_password");
		}
	}
}

function set_delpass(id) {
	if (document.getElementById(id).password) {
		with(document.getElementById(id)) {
			if(!password.value) password.value = get_password("pyib_password");
		}
	}
}

window.onunload=function(e) {
	if(style_cookie) {
		var title=get_active_stylesheet();
		set_cookie(style_cookie,title,365);
	}
}

window.onload=function(e) {
  checkhighlight();
  delandbanlinks();
  for(var i=0;i<hiddenthreads.length;i++){
    try {
      document.getElementById('unhidethread' + hiddenthreads[i]).style.display = 'block';
      document.getElementById('thread' + hiddenthreads[i]).style.display = 'none';
    } catch(err) {
      continue;
    }
  }
}

if(style_cookie) {
	var cookie = getCookie(style_cookie);
	var title = cookie ? cookie : get_preferred_stylesheet();

	set_stylesheet(title);
}

if (getCookie('pyib_staff')=='yes') {
	pyib_staff = true;
}

var hiddenthreads = getCookie('hiddenthreads').split('!');