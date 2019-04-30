$(document).ready(function(){
    $("#bs-example-navbar-collapse-1 ul").find('li').removeClass("active");
    $("#bs-example-navbar-collapse-1 ul").find('li').eq(4).addClass('active');

	var user_id = getCookie('user_id');
	function getCookie(name)
    {
        var arr,reg=new RegExp("(^| )"+name+"=([^;]*)(;|$)");
        if(arr=document.cookie.match(reg))
        	return unescape(arr[2]);
        else
        	return null;
    }
    
    function run_sentence_parse(pcid,cid,is_jump) {
		$.ajax({
           	url: '/new_reviews/sentence_parse_step',
            dataType: 'json',
            type: 'post',
            data: {'pcid': pcid, 'cid': cid,'user_id':user_id,'isjump':is_jump},
            success: function (result) {
                if(result.status=='1'){
                   alert('开始运行');
                   window.location.reload();
                }
                else{
                	alert("error");
				}
            }
        });
    }

    function run_features_extraction(pcid,cid,is_jump) {
    	var iscluster = $("#isclsuter").is(":checked");
		if(iscluster){iscluster = '1';}else{iscluster='0';}
		var cluster_alpha = parseFloat($("#cluster_alpha").val());
		var feature_limit = parseInt($("#feature_limit").val());
		$.ajax({
           	url: '/new_reviews/features_extraction_step',
            dataType: 'json',
            type: 'post',
            data: {'pcid': pcid, 'cid': cid,'user_id':user_id,'isjump':is_jump,'iscluster':iscluster,
            'cluster_alpha':cluster_alpha,'feature_limit':feature_limit},
            success: function (result) {
                if(result.status=='1'){
                   alert('开始运行');
                   window.location.reload();
                }
                else{
                	alert("error");
				}
            }
        });
    }

    function run_reviews_extraction(pcid,cid,is_jump) {
		$.ajax({
           	url: '/new_reviews/reviews_extraction_step',
            dataType: 'json',
            type: 'post',
            data: {'pcid': pcid, 'cid': cid,'user_id':user_id,'isjump':is_jump},
            success: function (result) {
                if(result.status=='1'){
                   alert('开始运行');
                   window.location.reload();
                }
                else{
                	alert("error");
				}
            }
        });
    }

    function jump_features_check(pcid,cid){
		$.ajax({
           	url: '/new_reviews/jump_features_check',
            dataType: 'json',
            type: 'post',
            data: {'pcid': pcid, 'cid': cid,'user_id':user_id},
            success: function (result) {
                if(result.status=='1'){
                   alert('开始运行');
                   window.location.reload();
                }
                else{
                	alert("error");
				}
            }
        });
	}
    
	function run_step(pcid,cid,step_num,is_jump){
		if(step_num == '1'){
			run_sentence_parse(pcid,cid,is_jump);
		}else if(step_num == '2'){
			run_features_extraction(pcid,cid,is_jump);
		}else if(step_num == '2_1'){
            window.location = "/new_reviews/word_clusters?pcid=" + pcid + "&cid=" + cid;
        }else if(step_num == '2_2'){
		    window.location = "/new_reviews/word_clusters?pcid=" + pcid + "&cid=" + cid;
        }else if(step_num == '3'){
			if(is_jump == '1'){
				jump_features_check(pcid,cid);
			}else{
				window.location = "/new_reviews/tags?pcid=" + pcid + "&cid=" + cid;
			}
		}else if(step_num == '4'){
			run_reviews_extraction(pcid,cid,is_jump);
		}
	}
    var action = null;
	var action_btn = null;
	$("#do_action").click(function () {
	    $('#myModal').modal('hide');
	    action.attr("disabled","disabled");
	    if(action) {
            var ele = action;
            var state = ele.attr("state");
            var step_num = ele.attr("step");
            var pcid = ele.attr("pcid");
            var cid = ele.attr("cid");
            var is_jump = ele.attr('is_jump');
            if (state == "go") {
                run_step(pcid, cid, step_num, is_jump);
            } else if (state == "no") {
                alert("请先完成之前的步骤!");
                action.removeAttr('disabled');
            } else if (state == "done") {
                alert("已经完成!");
                action.removeAttr('disabled');
            } else{
                action.removeAttr('disabled');
            }
            action = null;
        }
    });
	$(".text-step").click(function(e){
	    action = $(this);
	    $('#myModal').modal({keyboard: false});
	});

	$("#show-data").click(function(e){
		var pcid = $("#pcid").val();
		var cid = $("#cid").val();
		window.location = window.location.origin + window.location.pathname + "?pcid=" + pcid + "&cid=" + cid;
	});

	$("#show-synonym-global").click(function(e){
		window.location = '/new_reviews/lexicon/synonym_global/';
	});

	$("#show-target-global").click(function(e){
		window.location = '/new_reviews/lexicon/target_global/';
	});

	$("#show-synonym").click(function(e){
	    var $this = $(this);
		window.location = '/new_reviews/lexicon/synonym?pcid=' + $this.attr('pcid') + '&cid=' + $this.attr('cid');
	});

	$("#show-target").click(function(e){
	    var $this = $(this);
		window.location = '/new_reviews/lexicon/target?pcid=' + $this.attr('pcid') + '&cid=' + $this.attr('cid');
	});

	$("#show-sentiment").click(function(e){
	    var $this = $(this);
		window.location = '/new_reviews/sentiment?pcid=' + $this.attr('pcid') + '&cid=' + $this.attr('cid');
	});

	$("#show-sentiment-global").click(function(e){
	    var $this = $(this);
		window.location = '/new_reviews/sentiment/global/';
	});

	$("#create_state").click(function(e){
		var ele = $(this);
		var pcid = ele.attr('pcid');
		var cid = ele.attr('cid');
		$.ajax({
           	url: '/new_reviews/create_new_state',
            dataType: 'json',
            type: 'post',
            data: {'pcid': pcid, 'cid': cid},
            success: function (result) {
                if(result.status=='1'){
                alert(window.location.origin + window.location.pathname + "?pcid=" + pcid + "&cid=" + cid);
                   window.location = window.location.origin + window.location.pathname + "?pcid=" + pcid + "&cid=" + cid;
                }
                else{
                	alert("error");
				}
            }
        });
	});


	//reset status
    var reset_object = null;
    $("#open_reset_status_dialog").click(function () {
        reset_object = $(this);
        $('#myModal2').modal({keyboard: false});
    });
	$("#reset_status").click(function () {
	    $('#myModal2').modal('hide');
		var ele = reset_object;
		var pcid = ele.attr('pcid');
		var cid = ele.attr('cid');
		$.ajax({
           	url: '/new_reviews/reset_status',
            dataType: 'json',
            type: 'post',
            data: {'pcid': pcid, 'cid': cid,'user_id':user_id},
            success: function (result) {
                if(result.status=='1'){
                   window.location = window.location.origin + window.location.pathname + "?pcid=" + pcid + "&cid=" + cid;
                }
                else{
                	alert("error");
				}
            }
        });
    });
});
