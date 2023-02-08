# 저공해차 관리자 사이트:


(1) https://www.ev.or.kr/lcvms-mncpt/login.do ==> HTML
<form name="_loginForm" action="" method="post" autocomplete="off">
	<fieldset>
		<legend>로그인</legend>
		<p class="fl"><img src="/lcvms-mncpt/docs/img/login/ico_login.png" height="103" width="104" alt=""></p>
		<div class="inp_area">
			<label for="userId" class="hidden">아이디(ID)</label>
			<input type="text" name="userId" id="userId" title="아이디" class="filter:require:eng:num" style="width: 215px; height: 19px; background: none 0% 0% / auto repeat scroll padding-box border-box rgb(255, 255, 255);" lengthtype="length">
			<label for="userPw" class="hidden">비밀번호(PW)</label>
			<input type="password" name="userPw" id="userPw" title="비밀번호" class="filter:require:enter[doLogin]" style="width:215px;height:19px" lengthtype="length">
		</div>
		<a href="javascript:doLogin();" class="btn_login mt20"><span>로그인</span></a>
		
	</fieldset>
	</form>
							





# lcvms.js 파일 중 일부

/**
 * form DOM object 를 반환한다.
 *
 * @param form fromName or formId
 * @returns form object
 */
function getForm(form) { var formObj = null; if(typeof(form) == "object") { formObj = form; } else { var $formByName = $("form[name=" + form + "]"); var $formById = $("form").find("#" + form); if($formByName.length > 0) { formObj = $formByName[0]; } else if($formById.length > 0) { formObj = $formById[0]; }} return formObj;}


/**
 * submit 을 수행한다.
 *
 * @param form formName or formID
 * @param isBizSkip [option] service skip 여부
 * @param _target [option] target frameName
 * @param certOptions [option] 인증서관련옵션
 * @param ppcOptions [option] 휴대폰관련옵션
 */
function formSubmit(form, isBizSkip, _target, certOptions, ppcOptions) { var formObj = getForm(form); if(!ExtValidation.validate(formObj)) { return; } if(certOptions && certOptions["isCert"] === true) { PkiUtils.cert.setCertVidData(formObj, certOptions["certVid"], certOptions["certType"]); if(checkPkiCert()) { if(!PkiUtils.cert.setCertData(formObj, certOptions["certVid"], certOptions["certType"])) { return; } }} if(ppcOptions && ppcOptions["isPpc"] === true) { PpcUtil.setData(formObj, ppcOptions); } if(isSubmit) { return; } if(currentFocusElement) { $(currentFocusElement).blur(); } loadingBlock(true); var $formObj = $(formObj); $formObj.find("input[name=isProcess]").remove(); $formObj.append('<input type="hidden" name="isProcess" value="' + ((isBizSkip) ? "false" : "true") + '" />'); $formObj.attr("method", "post"); if (_target != null && _target != "") { $formObj.attr("target", _target); } isSubmit = true; if(checkPki()) { PkiUtils.setEncryptData(formObj, PkiUtils.getEncryptData(formObj)); } if(formObj != null) formObj.submit(); else $formObj.submit(); };



function checkPki() { var result = false; $.ajax({ type: "post", cache: false, url: CONTEXT_PATH + "/common/check/pki_check.jsp", async: false, dataType: "json", data: {}, complete: function(data, status) { var resultJson = JSON.parse(data.responseText); result = resultJson.result; } }); return result;};




/**
 * 로그인을 수행한다.
 */
function login() {
    var $loginForm = $(getForm("_loginForm"));
    $loginForm.attr("action", CONTEXT_PATH + "/j_spring_security_check");
    formSubmit($loginForm[0]);
}


/**
 * 로그아웃을 수행한다.
 */
function logout() {
    var $loginForm = $(getForm("_loginForm"));
    $loginForm.attr("action", CONTEXT_PATH + "/logout.do");
    formSubmit($loginForm[0]);
}
