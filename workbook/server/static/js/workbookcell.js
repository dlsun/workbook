//----------------------------------------------------------------------------
//  Copyright (C) 2008-2011  The IPython Development Team
//
//  Distributed under the terms of the BSD License.  The full license is in
//  the file COPYING, distributed as part of this software.
//----------------------------------------------------------------------------

//============================================================================
// WorkbookCell
//============================================================================

var IPython = (function (IPython) {

    var utils = IPython.utils;

    var WorkbookCell = function (notebook) {
        this.code_mirror = null;
        this.input_prompt_number = null;
        this.is_completing = false;
        this.completion_cursor = null;
        this.outputs = [];
        this.collapsed = false;
        this.tooltip_timeout = null;
        this.clear_out_timeout = null;
        this.read_only = true;
        IPython.Cell.apply(this, arguments);
    };


    WorkbookCell.prototype = new IPython.Cell();


    WorkbookCell.prototype.create_element = function () {
        var cell =  $('<div></div>').addClass('cell border-box-sizing code_cell vbox');
        cell.attr('tabindex','2');
        var input = $('<div></div>').addClass('input hbox');
        input.append($('<div/>').addClass('prompt input_prompt'));
        var input_area = $('<div/>').addClass('input_area box-flex1');
        this.code_mirror = CodeMirror(input_area.get(0), {
            indentUnit : 4,
            mode: 'python',
            theme: 'ipython',
            readOnly: "nocursor",
//             onKeyEvent: $.proxy(this.handle_codemirror_keyevent,this)
        });
        input.append(input_area);
        var output = $('<div></div>').addClass('output vbox');
        cell.append(output);
        this.element = cell;
        this.collapse();
    };

    //TODO, try to diminish the number of parameters.
    WorkbookCell.prototype.request_tooltip_after_time = function (pre_cursor,time){
        var that = this;
        if (pre_cursor === "" || pre_cursor === "(" ) {
            // don't do anything if line beggin with '(' or is empty
        } else {
            // Will set a timer to request tooltip in `time`
            that.tooltip_timeout = setTimeout(function(){
                    IPython.notebook.request_tool_tip(that, pre_cursor)
                },time);
        }
    };

    WorkbookCell.prototype.handle_codemirror_keyevent = function (editor, event) {
        // This method gets called in CodeMirror's onKeyDown/onKeyPress
        // handlers and is used to provide custom key handling. Its return
        // value is used to determine if CodeMirror should ignore the event:
        // true = ignore, false = don't ignore.
        
        if (this.read_only){
            return true;
        }
        
        // note that we are comparing and setting the time to wait at each key press.
        // a better wqy might be to generate a new function on each time change and
        // assign it to WorkbookCell.prototype.request_tooltip_after_time
        tooltip_wait_time = this.notebook.time_before_tooltip;
        tooltip_on_tab    = this.notebook.tooltip_on_tab;
        var that = this;
        // whatever key is pressed, first, cancel the tooltip request before
        // they are sent, and remove tooltip if any
        if(event.type === 'keydown' ) {
            that.remove_and_cancel_tooltip();
        };


        if (event.keyCode === 13 && (event.shiftKey || event.ctrlKey)) {
            // Always ignore shift-enter in CodeMirror as we handle it.
            return true;
        } else if (event.which === 40 && event.type === 'keypress' && tooltip_wait_time >= 0) {
            // triger aon keypress (!) otherwise inconsistent event.which depending on plateform
            // browser and keyboard layout !
            // Pressing '(' , request tooltip, don't forget to reappend it
            var cursor = editor.getCursor();
            var pre_cursor = editor.getRange({line:cursor.line,ch:0},cursor).trim()+'(';
            that.request_tooltip_after_time(pre_cursor,tooltip_wait_time);
        } else if (event.which === 38) {
            // If we are not at the top, let CM handle the up arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_top()) {
                event.stop();
                return false;
            } else {
                return true; 
            };
        } else if (event.which === 40) {
            // If we are not at the bottom, let CM handle the down arrow and
            // prevent the global keydown handler from handling it.
            if (!that.at_bottom()) {
                event.stop();
                return false;
            } else {
                return true; 
            };
        } else if (event.keyCode === 9 && event.type == 'keydown') {
            // Tab completion.
            var cur = editor.getCursor();
            //Do not trim here because of tooltip
            var pre_cursor = editor.getRange({line:cur.line,ch:0},cur);
            if (pre_cursor.trim() === "") {
                // Don't autocomplete if the part of the line before the cursor
                // is empty.  In this case, let CodeMirror handle indentation.
                return false;
            } else if ((pre_cursor.substr(-1) === "("|| pre_cursor.substr(-1) === " ") && tooltip_on_tab ) {
                that.request_tooltip_after_time(pre_cursor,0);
                // Prevent the event from bubbling up.
                event.stop();
                // Prevent CodeMirror from handling the tab.
                return true;
            } else {
                pre_cursor.trim();
                // Autocomplete the current line.
                event.stop();
                var line = editor.getLine(cur.line);
                this.is_completing = true;
                this.completion_cursor = cur;
                IPython.notebook.complete_cell(this, line, cur.ch);
                return true;
            };
        } else if (event.keyCode === 8 && event.type == 'keydown') {
            // If backspace and the line ends with 4 spaces, remove them.
            var cur = editor.getCursor();
            var line = editor.getLine(cur.line);
            var ending = line.slice(-4);
            if (ending === '    ') {
                editor.replaceRange('',
                    {line: cur.line, ch: cur.ch-4},
                    {line: cur.line, ch: cur.ch}
                );
                event.stop();
                return true;
            } else {
                return false;
            };
        } else {
            // keypress/keyup also trigger on TAB press, and we don't want to
            // use those to disable tab completion.
            if (this.is_completing && event.keyCode !== 9) {
                var ed_cur = editor.getCursor();
                var cc_cur = this.completion_cursor;
                if (ed_cur.line !== cc_cur.line || ed_cur.ch !== cc_cur.ch) {
                    this.is_completing = false;
                    this.completion_cursor = null;
                };
            };
            return false;
        };
        return false;
    };

    WorkbookCell.prototype.remove_and_cancel_tooltip = function() {
        // note that we don't handle closing directly inside the calltip
        // as in the completer, because it is not focusable, so won't
        // get the event.
        if (this.tooltip_timeout != null){
            clearTimeout(this.tooltip_timeout);
            $('#tooltip').remove();
            this.tooltip_timeout = null;
        }
    }

    WorkbookCell.prototype.finish_tooltip = function (reply) {
        // Extract call tip data; the priority is call, init, main.
        defstring = reply.call_def;
        if (defstring == null) { defstring = reply.init_definition; }
        if (defstring == null) { defstring = reply.definition; }

        docstring = reply.call_docstring;
        if (docstring == null) { docstring = reply.init_docstring; }
        if (docstring == null) { docstring = reply.docstring; }
        if (docstring == null) { docstring = "<empty docstring>"; }

        name=reply.name;

        var that = this;
        var tooltip = $('<div/>').attr('id', 'tooltip').addClass('tooltip');
        // remove to have the tooltip not Limited in X and Y
        tooltip.addClass('smalltooltip');
        var pre=$('<pre/>').html(utils.fixConsole(docstring));
        var expandlink=$('<a/>').attr('href',"#");
            expandlink.addClass("ui-corner-all"); //rounded corner
            expandlink.attr('role',"button");
            //expandlink.addClass('ui-button');
            //expandlink.addClass('ui-state-default');
        var expandspan=$('<span/>').text('Expand');
            expandspan.addClass('ui-icon');
            expandspan.addClass('ui-icon-plus');
        expandlink.append(expandspan);
        expandlink.attr('id','expanbutton');
        expandlink.click(function(){
            tooltip.removeClass('smalltooltip');
            tooltip.addClass('bigtooltip');
            $('#expanbutton').remove();
            setTimeout(function(){that.code_mirror.focus();}, 50);
        });
        var morelink=$('<a/>').attr('href',"#");
            morelink.attr('role',"button");
            morelink.addClass('ui-button');
            //morelink.addClass("ui-corner-all"); //rounded corner
            //morelink.addClass('ui-state-default');
        var morespan=$('<span/>').text('Open in Pager');
            morespan.addClass('ui-icon');
            morespan.addClass('ui-icon-arrowstop-l-n');
        morelink.append(morespan);
        morelink.click(function(){
            var msg_id = IPython.notebook.kernel.execute(name+"?");
            IPython.notebook.msg_cell_map[msg_id] = IPython.notebook.get_selected_cell().cell_id;
            that.remove_and_cancel_tooltip();
            setTimeout(function(){that.code_mirror.focus();}, 50);
        });

        var closelink=$('<a/>').attr('href',"#");
            closelink.attr('role',"button");
            closelink.addClass('ui-button');
            //closelink.addClass("ui-corner-all"); //rounded corner
            //closelink.adClass('ui-state-default'); // grey background and blue cross
        var closespan=$('<span/>').text('Close');
            closespan.addClass('ui-icon');
            closespan.addClass('ui-icon-close');
        closelink.append(closespan);
        closelink.click(function(){
            that.remove_and_cancel_tooltip();
            setTimeout(function(){that.code_mirror.focus();}, 50);
            });
        //construct the tooltip
        tooltip.append(closelink);
        tooltip.append(expandlink);
        tooltip.append(morelink);
        if(defstring){
            defstring_html = $('<pre/>').html(utils.fixConsole(defstring));
            tooltip.append(defstring_html);
        }
        tooltip.append(pre);
        var pos = this.code_mirror.cursorCoords();
        tooltip.css('left',pos.x+'px');
        tooltip.css('top',pos.yBot+'px');
        $('body').append(tooltip);

        // issues with cross-closing if multiple tooltip in less than 5sec
        // keep it comented for now
        // setTimeout(that.remove_and_cancel_tooltip, 5000);
    };

    // As you type completer
    WorkbookCell.prototype.finish_completing = function (matched_text, matches) {
        if(matched_text[0]=='%'){
            completing_from_magic = true;
            completing_to_magic = false;
        } else {
            completing_from_magic = false;
            completing_to_magic = false;
        }
        //return if not completing or nothing to complete
        if (!this.is_completing || matches.length === 0) {return;}

        // for later readability
        var key = { tab:9,
                    esc:27,
                    backspace:8,
                    space:32,
                    shift:16,
                    enter:13,
                    // _ is 95
                    isCompSymbol : function (code)
                        {
                        return (code > 64 && code <= 90)
                            || (code >= 97 && code <= 122)
                            || (code == 95)
                        },
                    dismissAndAppend : function (code)
                        {
                        chararr = '()[]+-/\\. ,=*'.split("");
                        codearr = chararr.map(function(x){return x.charCodeAt(0)});
                        return jQuery.inArray(code, codearr) != -1;
                        }

                    }

        // smart completion, sort kwarg ending with '='
        var newm = new Array();
        if(this.notebook.smart_completer)
        {
            kwargs = new Array();
            other = new Array();
            for(var i = 0 ; i<matches.length ; ++i){
                if(matches[i].substr(-1) === '='){
                    kwargs.push(matches[i]);
                }else{other.push(matches[i]);}
            }
            newm = kwargs.concat(other);
            matches = newm;
        }
        // end sort kwargs

        // give common prefix of a array of string
        function sharedStart(A){
            shared='';
            if(A.length == 1){shared=A[0]}
            if(A.length > 1 ){
                var tem1, tem2, s, A = A.slice(0).sort();
                tem1 = A[0];
                s = tem1.length;
                tem2 = A.pop();
                while(s && tem2.indexOf(tem1) == -1){
                    tem1 = tem1.substring(0, --s);
                }
                shared = tem1;
            }
            if (shared[0] == '%' && !completing_from_magic)
            {
                shared = shared.substr(1);
                return [shared, true];
            } else {
                return [shared, false];
            }
        }


        //try to check if the user is typing tab at least twice after a word
        // and completion is "done"
        fallback_on_tooltip_after = 2
        if(matches.length == 1 && matched_text === matches[0])
        {
            if(this.npressed >fallback_on_tooltip_after  && this.prevmatch==matched_text)
            {
                this.request_tooltip_after_time(matched_text+'(',0);
                return;
            }
            this.prevmatch = matched_text
            this.npressed = this.npressed+1;
        }
        else
        {
            this.prevmatch = "";
            this.npressed = 0;
        }
        // end fallback on tooltip
        //==================================
        // Real completion logic start here
        var that = this;
        var cur = this.completion_cursor;
        var done = false;

        // call to dismmiss the completer
        var close = function () {
            if (done) return;
            done = true;
            if (complete != undefined)
            {complete.remove();}
            that.is_completing = false;
            that.completion_cursor = null;
        };

        // update codemirror with the typed text
        prev = matched_text
        var update = function (inserted_text, event) {
            that.code_mirror.replaceRange(
                inserted_text,
                {line: cur.line, ch: (cur.ch-matched_text.length)},
                {line: cur.line, ch: (cur.ch+prev.length-matched_text.length)}
            );
            prev = inserted_text
            if(event != null){
                event.stopPropagation();
                event.preventDefault();
            }
        };
        // insert the given text and exit the completer
        var insert = function (selected_text, event) {
            update(selected_text)
            close();
            setTimeout(function(){that.code_mirror.focus();}, 50);
        };

        // insert the curent highlited selection and exit
        var pick = function () {
            insert(select.val()[0],null);
        };


        // Define function to clear the completer, refill it with the new
        // matches, update the pseuso typing field. autopick insert match if
        // only one left, in no matches (anymore) dismiss itself by pasting
        // what the user have typed until then
        var complete_with = function(matches,typed_text,autopick,event)
        {
            // If autopick an only one match, past.
            // Used to 'pick' when pressing tab
            var prefix = '';
            if(completing_to_magic && !completing_from_magic)
            {
                prefix='%';
            }
            if (matches.length < 1) {
                insert(prefix+typed_text,event);
                if(event != null){
                event.stopPropagation();
                event.preventDefault();
                }
            } else if (autopick && matches.length == 1) {
                insert(matches[0],event);
                if(event != null){
                event.stopPropagation();
                event.preventDefault();
                }
                return;
            }
            //clear the previous completion if any
            update(prefix+typed_text,event);
            complete.children().children().remove();
            $('#asyoutype').html("<b>"+prefix+matched_text+"</b>"+typed_text.substr(matched_text.length));
            select = $('#asyoutypeselect');
            for (var i = 0; i<matches.length; ++i) {
                    select.append($('<option/>').html(matches[i]));
            }
            select.children().first().attr('selected','true');
        }

        // create html for completer
        var complete = $('<div/>').addClass('completions');
            complete.attr('id','complete');
        complete.append($('<p/>').attr('id', 'asyoutype').html('<b>fixed part</b>user part'));//pseudo input field

        var select = $('<select/>').attr('multiple','true');
            select.attr('id', 'asyoutypeselect')
            select.attr('size',Math.min(10,matches.length));
        var pos = this.code_mirror.cursorCoords();

        // TODO: I propose to remove enough horizontal pixel
        // to align the text later
        complete.css('left',pos.x+'px');
        complete.css('top',pos.yBot+'px');
        complete.append(select);

        $('body').append(complete);

        // So a first actual completion.  see if all the completion start wit
        // the same letter and complete if necessary
        ff = sharedStart(matches)
        fastForward = ff[0];
        completing_to_magic = ff[1];
        typed_characters = fastForward.substr(matched_text.length);
        complete_with(matches,matched_text+typed_characters,true,null);
        filterd = matches;
        // Give focus to select, and make it filter the match as the user type
        // by filtering the previous matches. Called by .keypress and .keydown
        var downandpress = function (event,press_or_down) {
            var code = event.which;
            var autopick = false; // auto 'pick' if only one match
            if (press_or_down === 0){
                press = true; down = false; //Are we called from keypress or keydown
            } else if (press_or_down == 1){
                press = false; down = true;
            }
            if (code === key.shift) {
                // nothing on Shift
                return;
            }
            if (key.dismissAndAppend(code) && press) {
                var newchar = String.fromCharCode(code);
                typed_characters = typed_characters+newchar;
                insert(matched_text+typed_characters,event);
                return
            }
            if (code === key.enter) {
                // Pressing ENTER will cause a pick
                event.stopPropagation();
                event.preventDefault();
                pick();
            } else if (code === 38 || code === 40) {
                // We don't want the document keydown handler to handle UP/DOWN,
                // but we want the default action.
                event.stopPropagation();
            } else if ( (code == key.backspace)||(code == key.tab && down) || press  || key.isCompSymbol(code)){
                if( key.isCompSymbol(code) && press)
                {
                    var newchar = String.fromCharCode(code);
                    typed_characters = typed_characters+newchar;
                } else if (code == key.tab) {
                    ff = sharedStart(matches)
                    fastForward = ff[0];
                    completing_to_magic = ff[1];
                    ffsub = fastForward.substr(matched_text.length+typed_characters.length);
                    typed_characters = typed_characters+ffsub;
                    autopick = true;
                } else if (code == key.backspace && down) {
                    // cancel if user have erase everything, otherwise decrease
                    // what we filter with
                    event.preventDefault();
                    if (typed_characters.length <= 0)
                    {
                        insert(matched_text,event)
                        return
                    }
                    typed_characters = typed_characters.substr(0,typed_characters.length-1);
                } else if (press && code != key.backspace && code != key.tab && code != 0){
                    insert(matched_text+typed_characters,event);
                    return
                } else {
                    return
                }
                re = new RegExp("^"+"\%?"+matched_text+typed_characters,"");
                filterd = matches.filter(function(x){return re.test(x)});
                ff = sharedStart(filterd);
                completing_to_magic = ff[1];
                complete_with(filterd,matched_text+typed_characters,autopick,event);
            } else if (code == key.esc) {
                // dismiss the completer and go back to before invoking it
                insert(matched_text,event);
            } else if (press) { // abort only on .keypress or esc
            }
        }
        select.keydown(function (event) {
            downandpress(event,1)
        });
        select.keypress(function (event) {
            downandpress(event,0)
        });
        // Double click also causes a pick.
        // and bind the last actions.
        select.dblclick(pick);
        select.blur(close);
        select.focus();
    };


    WorkbookCell.prototype.select = function () {
        IPython.Cell.prototype.select.apply(this);
        this.code_mirror.refresh();
        this.code_mirror.focus();
        // We used to need an additional refresh() after the focus, but
        // it appears that this has been fixed in CM. This bug would show
        // up on FF when a newly loaded markdown cell was edited.
    };


    WorkbookCell.prototype.select_all = function () {
        var start = {line: 0, ch: 0};
        var nlines = this.code_mirror.lineCount();
        var last_line = this.code_mirror.getLine(nlines-1);
        var end = {line: nlines-1, ch: last_line.length};
        this.code_mirror.setSelection(start, end);
    };


    WorkbookCell.prototype.append_output = function (json, dynamic) {
        // If dynamic is true, javascript output will be eval'd.
        this.expand();
        this.flush_clear_timeout();
        if (json.output_type === 'pyout') {
            this.append_pyout(json, dynamic);
        } else if (json.output_type === 'pyerr') {
            this.append_pyerr(json);
        } else if (json.output_type === 'display_data') {
            this.append_display_data(json, dynamic);
        } else if (json.output_type === 'stream') {
            this.append_stream(json);
        };
        this.outputs.push(json);
    };


    WorkbookCell.prototype.create_output_area = function () {
        var oa = $("<div/>").addClass("hbox output_area");
        oa.append($('<div/>').addClass('prompt'));
        return oa;
    };


    WorkbookCell.prototype.append_pyout = function (json, dynamic) {
        n = json.prompt_number || ' ';
        var toinsert = this.create_output_area();
        toinsert.find('div.prompt').addClass('output_prompt').html('Out[' + n + ']:');
        this.append_mime_type(json, toinsert, dynamic);
        this.element.find('div.output').append(toinsert);
        // If we just output latex, typeset it.
        if ((json.latex !== undefined) || (json.html !== undefined)) {
            this.typeset();
        };
    };


    WorkbookCell.prototype.append_pyerr = function (json) {
        var tb = json.traceback;
        if (tb !== undefined && tb.length > 0) {
            var s = '';
            var len = tb.length;
            for (var i=0; i<len; i++) {
                s = s + tb[i] + '\n';
            }
            s = s + '\n';
            var toinsert = this.create_output_area();
            this.append_text(s, toinsert);
            this.element.find('div.output').append(toinsert);
        };
    };


    WorkbookCell.prototype.append_stream = function (json) {
        // temporary fix: if stream undefined (json file written prior to this patch),
        // default to most likely stdout:
        if (json.stream == undefined){
            json.stream = 'stdout';
        }
        if (!utils.fixConsole(json.text)){
            // fixConsole gives nothing (empty string, \r, etc.)
            // so don't append any elements, which might add undesirable space
            return;
        }
        var subclass = "output_"+json.stream;
        if (this.outputs.length > 0){
            // have at least one output to consider
            var last = this.outputs[this.outputs.length-1];
            if (last.output_type == 'stream' && json.stream == last.stream){
                // latest output was in the same stream,
                // so append directly into its pre tag
                // escape ANSI & HTML specials:
                var text = utils.fixConsole(json.text);
                this.element.find('div.'+subclass).last().find('pre').append(text);
                return;
            }
        }
        
        // If we got here, attach a new div
        var toinsert = this.create_output_area();
        this.append_text(json.text, toinsert, "output_stream "+subclass);
        this.element.find('div.output').append(toinsert);
    };


    WorkbookCell.prototype.append_display_data = function (json, dynamic) {
        var toinsert = this.create_output_area();
        this.append_mime_type(json, toinsert, dynamic);
        this.element.find('div.output').append(toinsert);
        // If we just output latex, typeset it.
        if ( (json.latex !== undefined) || (json.html !== undefined) ) {
            this.typeset();
        };
    };


    WorkbookCell.prototype.append_mime_type = function (json, element, dynamic) {
        if (json.javascript !== undefined && dynamic) {
            this.append_javascript(json.javascript, element, dynamic);
        } else if (json.html !== undefined) {
            this.append_html(json.html, element);
        } else if (json.latex !== undefined) {
            this.append_latex(json.latex, element);
        } else if (json.svg !== undefined) {
            this.append_svg(json.svg, element);
        } else if (json.png !== undefined) {
            this.append_png(json.png, element);
        } else if (json.jpeg !== undefined) {
            this.append_jpeg(json.jpeg, element);
        } else if (json.text !== undefined) {
            this.append_text(json.text, element);
        } else if (json.comments !== undefined) {
	    this.append_comments(json.comments, element);
	};
    };


    WorkbookCell.prototype.append_html = function (html, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_html rendered_html");
        toinsert.append(html);
        element.append(toinsert);
    };

    // for adding comments -- which are just latex cells
    WorkbookCell.prototype.append_comments = function (latex, element) {
        // This method cannot do the typesetting because the latex first has to
        // be on the page.
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_latex comments");
        toinsert.append(latex);
        element.append(toinsert);
    };

    WorkbookCell.prototype.delete_comments = function () {
	this.element.find("div.comments").parent("div.output_area").remove();
    }


    WorkbookCell.prototype.append_javascript = function (js, container) {
        // We just eval the JS code, element appears in the local scope.
        var element = $("<div/>").addClass("box_flex1 output_subarea");
        container.append(element);
        // Div for js shouldn't be drawn, as it will add empty height to the area.
        container.hide();
        // If the Javascript appends content to `element` that should be drawn, then
        // it must also call `container.show()`.
        eval(js);
    }


    WorkbookCell.prototype.append_text = function (data, element, extra_class) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_text");
        // escape ANSI & HTML specials in plaintext:
        data = utils.fixConsole(data);
        if (extra_class){
            toinsert.addClass(extra_class);
        }
        toinsert.append($("<pre/>").html(data));
        element.append(toinsert);
    };


    WorkbookCell.prototype.append_svg = function (svg, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_svg");
        toinsert.append(svg);
        element.append(toinsert);
    };


    WorkbookCell.prototype.append_png = function (png, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_png");
        toinsert.append($("<img/>").attr('src','data:image/png;base64,'+png));
        element.append(toinsert);
    };


    WorkbookCell.prototype.append_jpeg = function (jpeg, element) {
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_jpeg");
        toinsert.append($("<img/>").attr('src','data:image/jpeg;base64,'+jpeg));
        element.append(toinsert);
    };


    WorkbookCell.prototype.append_latex = function (latex, element) {
        // This method cannot do the typesetting because the latex first has to
        // be on the page.
        var toinsert = $("<div/>").addClass("box_flex1 output_subarea output_latex");
        toinsert.append(latex);
        element.append(toinsert);
    };


    WorkbookCell.prototype.clear_output = function (stdout, stderr, other) {
        var that = this;
        if (this.clear_out_timeout != null){
            // fire previous pending clear *immediately*
            clearTimeout(this.clear_out_timeout);
            this.clear_out_timeout = null;
            this.clear_output_callback(this._clear_stdout, this._clear_stderr, this._clear_other);
        }
        // store flags for flushing the timeout
        this._clear_stdout = stdout;
        this._clear_stderr = stderr;
        this._clear_other = other;
        this.clear_out_timeout = setTimeout(function(){
            // really clear timeout only after a short delay
            // this reduces flicker in 'clear_output; print' cases
            that.clear_out_timeout = null;
            that._clear_stdout = that._clear_stderr = that._clear_other = null;
            that.clear_output_callback(stdout, stderr, other);
        }, 500
        );
    };
    
    WorkbookCell.prototype.clear_output_callback = function (stdout, stderr, other) {
        var output_div = this.element.find("div.output");
        
        if (stdout && stderr && other){
            // clear all, no need for logic
            output_div.html("");
            this.outputs = [];
            return;
        }
        // remove html output
        // each output_subarea that has an identifying class is in an output_area
        // which is the element to be removed.
        if (stdout){
            output_div.find("div.output_stdout").parent().remove();
        }
        if (stderr){
            output_div.find("div.output_stderr").parent().remove();
        }
        if (other){
            output_div.find("div.output_subarea").not("div.output_stderr").not("div.output_stdout").parent().remove();
        }
        
        // remove cleared outputs from JSON list:
        for (var i = this.outputs.length - 1; i >= 0; i--){
            var out = this.outputs[i];
            var output_type = out.output_type;
            if (output_type == "display_data" && other){
                this.outputs.splice(i,1);
            }else if (output_type == "stream"){
                if (stdout && out.stream == "stdout"){
                    this.outputs.splice(i,1);
                }else if (stderr && out.stream == "stderr"){
                    this.outputs.splice(i,1);
                }
            }
        }
    };


    WorkbookCell.prototype.clear_input = function () {
        this.code_mirror.setValue('');
    };
    
    WorkbookCell.prototype.flush_clear_timeout = function() {
        var output_div = this.element.find('div.output');
        if (this.clear_out_timeout){
            clearTimeout(this.clear_out_timeout);
            this.clear_out_timeout = null;
            this.clear_output_callback(this._clear_stdout, this._clear_stderr, this._clear_other);
        };
    }


    WorkbookCell.prototype.collapse = function () {
        if (!this.collapsed) {
            this.element.find('div.output').hide();
            this.collapsed = true;
        };
    };


    WorkbookCell.prototype.expand = function () {
        if (this.collapsed) {
            this.element.find('div.output').show();
            this.collapsed = false;
        };
    };


    WorkbookCell.prototype.toggle_output = function () {
        if (this.collapsed) {
            this.expand();
        } else {
            this.collapse();
        };
    };

    WorkbookCell.prototype.set_input_prompt = function (number) {
        this.input_prompt_number = number;
        var ns = number || "&nbsp;";
        this.element.find('div.input_prompt').html('In&nbsp;[' + ns + ']:');
    };


    WorkbookCell.prototype.get_text = function () {
        return this.code_mirror.getValue();
    };


    WorkbookCell.prototype.set_text = function (code) {
        return this.code_mirror.setValue(code);
    };


    WorkbookCell.prototype.at_top = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === 0) {
            return true;
        } else {
            return false;
        }
    };


    WorkbookCell.prototype.at_bottom = function () {
        var cursor = this.code_mirror.getCursor();
        if (cursor.line === (this.code_mirror.lineCount()-1)) {
            return true;
        } else {
            return false;
        }
    };


    WorkbookCell.prototype.fromJSON = function (data) {
        if (data.cell_type === 'workbook') {
            if (data.input !== undefined) {
                this.set_text(data.input);
            }
            if (data.prompt_number !== undefined) {
                this.set_input_prompt(data.prompt_number);
            } else {
                this.set_input_prompt();
            };
            var len = data.outputs.length;
            for (var i=0; i<len; i++) {
                // append with dynamic=false.
                this.append_output(data.outputs[i], false);
            };
            if (data.collapsed !== undefined) {
                if (data.collapsed) {
                    this.collapse();
                } else {
                    this.expand();
                };
            };
        };
    };


    WorkbookCell.prototype.toJSON = function () {
        var data = {};
        data.input = this.get_text();
        data.cell_type = 'code'; // Turn the cell back to 'code' for saving 
        if (this.input_prompt_number) {
            data.prompt_number = this.input_prompt_number;
        };
        var outputs = [];
        var len = this.outputs.length;
        for (var i=0; i<len; i++) {
            outputs[i] = this.outputs[i];
        };
        data.outputs = outputs;
        data.language = 'python';
        data.collapsed = this.collapsed;
        return data;
    };


    IPython.WorkbookCell = WorkbookCell;

    return IPython;
}(IPython));
